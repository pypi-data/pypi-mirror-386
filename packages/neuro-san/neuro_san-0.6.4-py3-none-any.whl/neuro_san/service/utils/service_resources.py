
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT
"""
See class definition for comments.
"""
import os
import sys
import stat
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
import psutil

# Unix-only
try:
    # pylint: disable=invalid-name
    import resource  # not available on Windows
except Exception:  # pylint: disable=broad-exception-caught
    resource = None


class ServiceResources:
    """
    Class provides utility methods to monitor usage
    of service run-time resources,
    like:
    - Unix/macOS: file descriptors (FDs) by type
    - Windows: OS handles breakdown (files vs INET sockets) + total handles
    """
    on_unix: bool = sys.platform.startswith("linux")
    on_macos: bool = sys.platform.startswith("darwin")
    on_windows: bool = sys.platform.startswith("win")

    # ---------------------------
    # POSIX helpers (Linux/macOS)
    # ---------------------------
    @classmethod
    def _iter_fds_posix(cls):
        """
        Iterator over numeric FDs for the current process (Unix/macOS).
        """
        fd_dir = "/proc/self/fd" if cls.on_unix else "/dev/fd"
        try:
            names = os.listdir(fd_dir)
        except Exception:  # pylint: disable=broad-exception-caught
            # directory may not exist in some rare environments
            return
        for name in names:
            try:
                fd = int(name)
            except Exception:  # pylint: disable=broad-exception-caught
                continue
            yield fd

    @classmethod
    def _classify_fds_posix(cls) -> Dict[str, int]:
        """
        Returns counts by FD kind on Unix/macOS:
          regular_file, socket_inet, socket_unix, fifo_pipe, other, total
        """
        p = psutil.Process()

        # Maps of socket FDs to distinguish AF_INET vs AF_UNIX
        inet_fds = {c.fd for c in p.connections(kind="inet")}  # tcp/udp
        unix_fds = {c.fd for c in p.connections(kind="unix")}  # unix sockets

        fd_dict: Dict[str, int] = {}
        total_fds = 0

        for fd in cls._iter_fds_posix() or ():
            try:
                st = os.fstat(fd)
            except OSError:
                continue  # fd may have just closed
            mode = st.st_mode

            if stat.S_ISREG(mode):
                kind = "regular_file"
            elif stat.S_ISSOCK(mode):
                if fd in inet_fds:
                    kind = "socket_inet"
                elif fd in unix_fds:
                    kind = "socket_unix"
                else:
                    kind = "other"  # socket but not recognized by psutil maps
            elif stat.S_ISFIFO(mode):
                kind = "fifo_pipe"
            else:
                kind = "other"

            total_fds += 1
            fd_dict[kind] = fd_dict.get(kind, 0) + 1

        fd_dict["total"] = total_fds
        # ensure all expected keys exist (helpful for stable metrics)
        for k in ("regular_file", "socket_inet", "socket_unix", "fifo_pipe", "other"):
            fd_dict.setdefault(k, 0)
        return fd_dict

    # ---------------------------
    # Windows helpers
    # ---------------------------
    @classmethod
    def _classify_handles_windows(cls) -> Dict[str, int]:
        """
        Returns a simplified breakdown on Windows using psutil:

          regular_file   -> len(Process.open_files())
          socket_inet    -> len(Process.connections(kind="inet"))
          other_handles  -> num_handles - above_known
          total_handles  -> Process.num_handles()

        Notes:
          * Windows does not expose POSIX FDs; we count OS handles instead.
          * We cannot reliably enumerate every handle type without native WinAPI.
        """
        p = psutil.Process()

        try:
            total_handles = p.num_handles()  # all handles owned by this process
        except Exception:  # pylint: disable=broad-exception-caught
            total_handles = 0
        files = len(p.open_files())
        # TCP/UDP INET sockets for this process
        inet_conns = p.connections(kind="inet")
        socket_inet = len(inet_conns)

        # We can't see AF_UNIX on Windows (not applicable), FIFO pipes classification requires WinAPI.
        # Derive "other_handles" as the remainder; never let it go negative.
        known = files + socket_inet
        other_handles = max(total_handles - known, 0)

        return {
            "regular_file": files,
            "socket_inet": socket_inet,
            "socket_unix": 0,         # not applicable on Windows
            "fifo_pipe": 0,           # not available via psutil alone
            "other_handles": other_handles,
            "total_handles": total_handles,
        }

    # ---------------------------
    # Public API (cross-platform)
    # ---------------------------
    @classmethod
    def classify_fds(cls) -> Dict[str, int]:
        """
        Cross-platform classification:
          * Unix/macOS: returns per-FD kinds + "total"
          * Windows:    returns per-handle kinds + "total_handles"
        """
        if cls.on_unix or cls.on_macos:
            return cls._classify_fds_posix()
        if cls.on_windows:
            return cls._classify_handles_windows()
        # Fallback: try POSIX path; if not, return minimal info
        try:
            return cls._classify_fds_posix()
        except Exception:  # pylint: disable=broad-exception-caught
            p = psutil.Process()
            return {"total_unknown": getattr(p, "num_fds", lambda: 0)()}

    @classmethod
    def get_fd_usage(cls) -> Tuple[Dict[str, int], Optional[int], Optional[int]]:
        """
        Returns (counts_dict, soft_limit, hard_limit).

        * Unix/macOS: soft/hard are RLIMIT_NOFILE integers.
        * Windows:    returns (counts_dict, None, None) since RLIMIT_NOFILE does not apply.
        """
        counts = cls.classify_fds()

        if (cls.on_unix or cls.on_macos) and resource is not None:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            return counts, soft, hard

        # Windows / unknown
        return counts, None, None

    # --- internal helper: get this process's TCP connections, psutil-6-safe ---
    @classmethod
    def _proc_tcp_conns(cls) -> List[Any]:
        """
        Return TCP connections for the current process, with a fallback that
        is compatible with psutil 6.x where Process.connections may be deprecated.
        """
        p = psutil.Process()
        try:
            # Works on psutil <= 5.x and (for now) also on many 6.x installs
            return p.connections(kind="tcp")
        except Exception:  # pylint: disable=broad-exception-caught
            # psutil 6.x style: filter system-wide by pid
            conns = []
            for c in psutil.net_connections(kind="tcp"):
                if getattr(c, "pid", None) == p.pid:
                    conns.append(c)
            return conns

    # --- unchanged external API, but hardened for Windows/psutil variations ---
    @classmethod
    def classify_outbound_sockets(cls, outbound_tcp: Iterable[Any]) -> Dict[str, Any]:
        """
        Classify outbound process socket connections by remote address and status.

        Cross-platform notes:
          * Windows/macOS/Linux all provide per-process TCP connections via psutil.
          * Some entries may have missing raddr (e.g., early handshake) — we bucket those under "(no-remote)".
          * Status names are strings from psutil (e.g., 'ESTABLISHED','TIME_WAIT', etc.).
        """
        result: Dict[str, Dict[str, int]] = {}

        for conn in outbound_tcp:
            # Normalize remote address: "ip:port" or "(no-remote)"
            if conn.raddr:
                try:
                    rip = getattr(conn.raddr, "ip", None)
                    rport = getattr(conn.raddr, "port", None)
                    if rip is None or rport is None:
                        # Fallback to repr if platform provides a different shape
                        sock_addr = str(conn.raddr)
                    else:
                        sock_addr = f"{rip}:{rport}"
                except Exception:  # pylint: disable=broad-exception-caught
                    # Very defensive: some psutil versions/platforms might differ
                    sock_addr = str(conn.raddr)
            else:
                sock_addr = "(no-remote)"

            bucket = result.setdefault(sock_addr, {})
            sock_status: str = str(getattr(conn, "status", "UNKNOWN"))
            bucket[sock_status] = bucket.get(sock_status, 0) + 1

        return result

    @classmethod
    def classify_sockets(cls, server_port: int) -> Dict[str, Any]:
        """
        Classify active sockets bound to the given server port.
        :param server_port: server port
        :return: dictionary with keys:
           "inbound_listen": number of inbound listening sockets;
           "inbound_accepted": number of accepted inbound connections;
           "outbound_tcp": dictionary describing outbound connections.

        Cross-platform behavior:
          * Works on Linux/macOS/Windows using per-process TCP enumeration.
          * Dual-stack listeners typically appear as separate IPv4/IPv6 LISTEN sockets.
          * Multi-process servers (Tornado server.start(N)) must call this in each worker PID.
        """
        tcp = cls._proc_tcp_conns()

        inbound_listen = 0
        inbound_accepted_list: list = []
        outbound_list: list = []

        for c in tcp:
            lport = c.laddr.port if c.laddr else None
            status = getattr(c, "status", None)

            # LISTEN socket on our server port?
            if status == psutil.CONN_LISTEN and lport == server_port:
                inbound_listen += 1
                continue

            # Accepted inbound socket uses the server port as local port
            if lport == server_port and status != psutil.CONN_LISTEN:
                inbound_accepted_list.append(c)
                continue

            # Everything else is an outbound (client) socket from this process
            outbound_list.append(c)

        return {
            "inbound_listen": inbound_listen,
            "inbound_accepted": len(inbound_accepted_list),
            "outbound_tcp": cls.classify_outbound_sockets(outbound_list),
        }
