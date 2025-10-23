import os
import threading
import subprocess
import time
from typing import Callable, Dict, Optional

class CLASS_ExtWrapper7z:
    def __init__(self, Pms_7z_path: Optional[str] = None):
        self.Pms_7z_path = Pms_7z_path or self.CUF_Find7zPath()
        self.tasks: Dict[int, Dict] = {}
        self.task_counter = 0
        self.lock = threading.Lock()

    # 🔍 自動搜尋 7z.exe
    def CUF_Find7zPath(self) -> Optional[str]:
        common_paths = [
            r"C:\\Program Files\\7-Zip\\7z.exe",
            r"C:\\Program Files (x86)\\7-Zip\\7z.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path

        for root, dirs, files in os.walk("C:\\"):
            if "7z.exe" in files:
                return os.path.join(root, "7z.exe")
        return None

    # 📦 建立壓縮或解壓縮任務
    def CUF_AddTask(
        self,
        Pms_Mode: str,  # "compress" 或 "extract"
        Pms_InputPath: str,
        Pms_OutputPath: str,
        Pmi_VolumeSizeMB: int = 0,
        Pms_Password: str = "",
        Pmf_Callback: Optional[Callable[[int, float, str], None]] = None,
    ) -> int:
        with self.lock:
            self.task_counter += 1
            mi_TaskID = self.task_counter
            self.tasks[mi_TaskID] = {
                "thread": None,
                "progress": 0.0,
                "status": "queued",
                "cancel": False,
                "mode": Pms_Mode,
                "input": Pms_InputPath,
                "output": Pms_OutputPath,
                "callback": Pmf_Callback,
            }

        thread = threading.Thread(
            target=self._CUF_RunTask,
            args=(mi_TaskID, Pms_Mode, Pms_InputPath, Pms_OutputPath, Pmi_VolumeSizeMB, Pms_Password),
            daemon=True,
        )
        self.tasks[mi_TaskID]["thread"] = thread
        thread.start()
        return mi_TaskID

    # 🧩 執行壓縮/解壓縮
    def _CUF_RunTask(self, TaskID, Mode, InputPath, OutputPath, VolumeSizeMB, Password):
        task = self.tasks[TaskID]
        task["status"] = "running"
        Pms_7z_path = self.Pms_7z_path
        if not Pms_7z_path or not os.path.exists(Pms_7z_path):
            task["status"] = "error"
            if task["callback"]:
                task["callback"](TaskID, 0, "7z.exe not found")
            return

        if Mode == "compress":
            cmd = [Pms_7z_path, "a", OutputPath, "-y"]
            # 🔹 支援多個檔案/資料夾；以 ; 分隔
            paths = [p.strip() for p in InputPath.split(";") if p.strip()]
            cmd.extend(paths)
            if Password:
                cmd.append(f"-p{Password}")
            if VolumeSizeMB > 0:
                cmd.append(f"-v{VolumeSizeMB}m")

        elif Mode == "extract":
            cmd = [Pms_7z_path, "x", InputPath, f"-o{OutputPath}", "-y"]
            if Password:
                cmd.append(f"-p{Password}")
        else:
            task["status"] = "error"
            if task["callback"]:
                task["callback"](TaskID, 0, "Invalid mode")
            return

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        for line in proc.stdout:
            if task["cancel"]:
                proc.terminate()
                task["status"] = "cancelled"
                if task["callback"]:
                    task["callback"](TaskID, task["progress"], "Cancelled")
                return

            if "%" in line:
                try:
                    percent = float(line.strip().split("%")[0].split()[-1])
                    task["progress"] = percent
                    if task["callback"]:
                        task["callback"](TaskID, percent, "running")
                except:
                    pass

        proc.wait()
        if proc.returncode == 0 and not task["cancel"]:
            task["status"] = "done"
            task["progress"] = 100.0
            if task["callback"]:
                task["callback"](TaskID, 100.0, "done")
        elif not task["cancel"]:
            task["status"] = "error"
            if task["callback"]:
                task["callback"](TaskID, task["progress"], "error")

    # ❌ 取消任務
    def CUF_CancelTask(self, Pmi_TaskID: int):
        if Pmi_TaskID in self.tasks:
            self.tasks[Pmi_TaskID]["cancel"] = True

    # 📊 查詢所有任務總進度
    def CUF_GetTotalProgress(self) -> float:
        with self.lock:
            if not self.tasks:
                return 0.0
            total = sum(task["progress"] for task in self.tasks.values())
            return total / len(self.tasks)

    # 🔍 查詢任務狀態
    def CUF_GetTaskStatus(self, Pmi_TaskID: int) -> str:
        return self.tasks.get(Pmi_TaskID, {}).get("status", "unknown")




# ================================================================================
# === 測試範例 ===
if(__name__ == "__main__"):
    def my_callback(TaskID, progress, status):
        print(f"[Task {TaskID}] {status} - {progress:.1f}%")

    wrapper = CLASS_ExtWrapper7z()
    print("7z 路徑:", wrapper.Pms_7z_path)

    # 壓縮多個檔案 (同時支援萬用字元與多個資料夾)
    task1 = wrapper.CUF_AddTask(
        "compress",
        Pms_InputPath=r"C:\\Temp\\Rubber\b1*.bmp;C:\\boost\\more",
        Pms_OutputPath=r"C:\\TEMP\\OKOKO_GOOD.7z",
        Pmi_VolumeSizeMB=50,
        Pmf_Callback=my_callback,
    )

    while True:
        total_progress = wrapper.CUF_GetTotalProgress()
        print(f"總進度: {total_progress:.2f}%")
        time.sleep(2)
