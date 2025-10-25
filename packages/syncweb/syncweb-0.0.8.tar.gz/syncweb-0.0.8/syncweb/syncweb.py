import fnmatch, os
from pathlib import Path

from syncweb import str_utils
from syncweb.cmds.folders import conform_pending_folders
from syncweb.log_utils import log
from syncweb.syncthing import SyncthingNode


class Syncweb(SyncthingNode):
    def cmd_accept(self, device_ids):
        device_count = 0
        for path in device_ids:
            try:
                device_id = str_utils.extract_device_id(path)
                self.add_device(deviceID=device_id)
                device_count += 1
            except ValueError:
                log.error("Invalid Device ID %s", path)

        return device_count

    def cmd_pause(self, device_ids=None):
        if device_ids is None:
            return self.pause()

        device_count = 0
        for path in device_ids:
            try:
                device_id = str_utils.extract_device_id(path)
                self.pause(device_id)
                device_count += 1
            except ValueError:
                log.error("Invalid Device ID %s", path)

        return device_count

    def cmd_resume(self, device_ids=None):
        if device_ids is None:
            return self.resume()

        device_count = 0
        for path in device_ids:
            try:
                device_id = str_utils.extract_device_id(path)
                self.resume(device_id)
                device_count += 1
            except ValueError:
                log.error("Invalid Device ID %s", path)

        return device_count

    def create_folder_id(self, path):
        existing_folders = set(self.folder_stats().keys())

        name = str_utils.basename(path)
        if name not in existing_folders:
            return name

        return str_utils.path_hash(path)

    def cmd_init(self, paths):
        folder_count = 0
        for path in paths:
            os.makedirs(path, exist_ok=True)
            path = os.path.realpath(path)

            folder_id = self.create_folder_id(path)
            self.add_folder(id=folder_id, label=str_utils.basename(path), path=path, type="sendonly")
            self.set_ignores(folder_id, lines=[])
            print(f"sync://{folder_id}#{self.device_id}")
            folder_count += 1
        return folder_count

    def cmd_join(self, urls, prefix=".", decode=True):
        device_count, folder_count = 0, 0
        for url in urls:
            ref = str_utils.parse_syncweb_path(url, decode=decode)
            if ref.device_id:
                self.add_device(deviceID=ref.device_id)
                device_count += 1

            if ref.folder_id:
                default_path = os.path.realpath(prefix)
                path = os.path.join(default_path, ref.folder_id)
                os.makedirs(path, exist_ok=True)

                folder_id = self.create_folder_id(path)
                if path not in self.folder_roots:
                    self.add_folder(id=folder_id, path=path, type="receiveonly", paused=True)
                    self.set_ignores(folder_id)
                    self.resume_folder(folder_id)
                    folder_count += 1

                if ref.device_id:
                    self.add_folder_devices(ref.folder_id, [ref.device_id])

                if ref.subpath:
                    # TODO: ask to confirm if ref.subpath == "/" ?
                    # or check size first?
                    self.add_ignores(folder_id, [ref.subpath])

        return device_count, folder_count

    def add_ignores(self, folder_id: str, unignores: list[str]):
        existing = set(s for s in self.ignores(folder_id)["ignore"] if not s.startswith("// Syncweb-managed"))

        new = set()
        for p in unignores:
            if p.startswith("//"):
                continue
            if not p.startswith("!/"):
                p = "!/" + p
            new.add(p)

        combined = new.union(existing)
        ordered = (
            ["// Syncweb-managed"]
            + sorted([p for p in combined if p.startswith("!")])
            + sorted([p for p in combined if not p.startswith("!") and p != "*"])
            + ["*"]
        )

        self.set_ignores(folder_id, lines=ordered)

    def device_short2long(self, short):
        matches = [d for d in self.devices_list if d.startswith(short)]
        if len(matches) == 1:
            dev_id = matches[0]
            return dev_id
        return None

    def device_long2name(self, long):
        short = long[:7]

        try:
            name = self.devices_dict[long].get("name")
            if not name or name.lower() in ("syncweb", "syncthing"):
                return short
            return f"{name} ({short})"
        except KeyError:
            return f"{short}-???????"

    def accept_pending_devices(self):
        pending = self.pending_devices()
        if not pending:
            log.info(f"[%s] No pending devices", self.name)
            return

        existing_devices = self.devices()
        existing_device_ids = {d["deviceID"] for d in existing_devices}

        for dev_id, info in pending.items():
            if dev_id in existing_device_ids:
                log.info(f"[%s] Device %s already exists!", self.name, dev_id)
                continue

            name = info.get("name", dev_id[:7])
            log.info(f"[%s] Accepting device %s (%s)", self.name, name, dev_id)
            cfg = {
                "deviceID": dev_id,
                "name": name,
                "addresses": info.get("addresses") or [],
                "compression": "metadata",
                "introducer": False,
            }
            self._put(f"config/devices/{dev_id}", json=cfg)

    def join_pending_folders(self, folder_id: str | None = None):
        pending = conform_pending_folders(self.pending_folders())
        if not pending:
            log.info(f"[%s] No pending folders", self.name)
            return
        if folder_id:
            pending = [f for f in pending if f["id"] == folder_id]
            if not pending:
                log.info(f"[%s] No pending folders matching '%s'", self.name, folder_id)
                return

        existing_folders = self.folders()
        existing_folder_ids = {f["id"]: f for f in existing_folders}

        for folder in pending:
            fid = folder["id"]
            offered_by = folder.get("offeredBy", {}) or {}
            device_ids = list(offered_by.keys())

            if not device_ids:
                log.info(f"[%s] No devices offering folder '%s'", self.name, fid)
                continue

            if fid in existing_folder_ids:  # folder exists; just add new devices
                self.add_folder_devices(fid, device_ids)
            else:  # folder doesn't exist; create it (with devices)
                log.info(f"[%s] Creating folder '%s'", self.name, fid)
                cfg = {
                    "id": fid,
                    "label": fid,
                    "path": str(self.home / fid),
                    "type": "receiveonly",  # TODO: think
                    "devices": [{"deviceID": d} for d in device_ids],
                }
                self._post("config/folders", json=cfg)

    def _is_ignored(self, rel_path: Path, patterns: list[str]) -> bool:
        s = str(rel_path)
        for pat in patterns:
            if fnmatch.fnmatch(s, pat):
                return True
            if fnmatch.fnmatch(s + "/", pat):  # match directories
                return True
        return False
