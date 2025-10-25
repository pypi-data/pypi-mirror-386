import os
import pandas as pd
import psutil


def filter_perfdata(cell_history_data, perfdata, compress_idle=True):
    """Filter performance data to remove idle periods if requested"""
    if cell_history_data is None or cell_history_data.empty:
        return perfdata.iloc[0:0]

    if compress_idle:
        # Remove idle periods between cells
        # Create time masks for each cell's execution period
        masks = []
        for _, cell in cell_history_data.iterrows():
            mask = (perfdata["time"] >= cell["start_time"]) & (
                perfdata["time"] <= cell["end_time"]
            )
            masks.append(mask)

        if masks:
            combined_mask = pd.concat(masks, axis=1).any(axis=1)
            return perfdata[combined_mask]
        else:
            return perfdata.iloc[0:0]
    else:
        """Get start time from first cell and end time from last cell in the
        range"""
        start_time = cell_history_data.iloc[0]["start_time"]
        end_time = cell_history_data.iloc[-1]["end_time"]
        return perfdata[
            (perfdata["time"] >= start_time) & (perfdata["time"] <= end_time)
        ]


def is_slurm_available():
    """Check if SLURM is available by checking for SLURM_JOB_ID environment
    variable"""
    return os.environ.get("SLURM_JOB_ID") is not None


def get_available_levels():
    """Get list of available performance monitoring levels"""
    base_levels = ["user", "process", "system"]
    if is_slurm_available():
        base_levels.append("slurm")
    return base_levels


def detect_cgroup_version():
    """Detect if system is using cgroup v1 or v2"""
    return (
        "v2" if os.path.exists("/sys/fs/cgroup/cgroup.controllers") else "v1"
    )


def detect_memory_limit(level, uid, slurm_job):
    """Detect memory limit for a given level"""
    system_mem = round(psutil.virtual_memory().total / (1024**3), 2)

    if level == "slurm":
        paths = (
            [
                f"/sys/fs/cgroup/memory/slurm/uid_{uid}/job_{slurm_job}/"
                "memory.limit_in_bytes"
            ]
            if detect_cgroup_version() == "v1"
            else [
                f"/sys/fs/cgroup/system.slice/slurmstepd.scope/"
                f"job_{slurm_job}/memory.max",
                f"/sys/fs/cgroup/system.slice/slurm.service/job_{slurm_job}/"
                "memory.max",
                f"/sys/fs/cgroup/slurm/uid_{uid}/job_{slurm_job}/memory.max",
            ]
        )

        for path in paths:
            if os.path.exists(path):
                with open(path) as f:
                    limit = f.read().strip()
                    if limit != "max":
                        return round(int(limit) / (1024**3), 2)
    elif level == "process":
        try:
            import resource

            rlimit = resource.getrlimit(resource.RLIMIT_AS)[0]
            if rlimit != resource.RLIM_INFINITY:
                return round(rlimit / (1024**3), 2)
        except Exception:
            pass

    return system_mem
