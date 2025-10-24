import logging
import subprocess
import shutil
import tempfile
from pathlib import Path

logger = logging.getLogger("androsing")

class AndroSignError(Exception):
    pass

def find_executable(name):
    path = shutil.which(name)
    if not path:
        logger.error(f"Executable not found: {name}")
    return path

def run_cmd(cmd, capture_output=False):
    logger.debug(f"Running command: {' '.join(cmd)}")
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE,
            check=True,
        )
        if capture_output:
            out = res.stdout.decode("utf-8", errors="replace")
            logger.debug(out)
            return out
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
        logger.error(f"Command failed: {cmd}\n{err}")
        raise AndroSignError(err)

def sign_v1(apk_path, keystore, key_alias, ks_pass=None, key_pass=None):
    jarsigner = find_executable("jarsigner")
    if not jarsigner:
        raise AndroSignError("jarsigner not found in PATH.")
    cmd = [jarsigner, "-keystore", keystore]
    if ks_pass: cmd += ["-storepass", ks_pass]
    if key_pass: cmd += ["-keypass", key_pass]
    cmd += ["-sigalg", "SHA256withRSA", "-digestalg", "SHA-256"]
    cmd += [str(apk_path), key_alias]
    run_cmd(cmd)
    logger.info("V1 signing complete.")

def align_apk(apk_path):
    zipalign = find_executable("zipalign")
    if not zipalign:
        logger.warning("zipalign not found; skipping alignment.")
        return apk_path
    out = Path(apk_path).with_suffix(".aligned.apk")
    run_cmd([zipalign, "-p", "4", str(apk_path), str(out)])
    logger.info(f"APK aligned -> {out}")
    return str(out)

def sign_v2(apk_path, keystore=None, key_alias=None, ks_pass=None, key_pass=None):
    apksigner = find_executable("apksigner")
    if not apksigner:
        raise AndroSignError("apksigner not found in PATH.")
    cmd = [apksigner, "sign"]
    if keystore:
        cmd += ["--ks", keystore]
        if ks_pass: cmd += ["--ks-pass", f"pass:{ks_pass}"]
        if key_pass: cmd += ["--key-pass", f"pass:{key_pass}"]
        if key_alias: cmd += ["--ks-key-alias", key_alias]
    cmd += [str(apk_path)]
    run_cmd(cmd)
    logger.info("V2 signing complete.")

def verify(apk_path):
    apksigner = find_executable("apksigner")
    if not apksigner:
        logger.warning("apksigner not found; skipping verify.")
        return False
    try:
        output = run_cmd([apksigner, "verify", "--print-certs", str(apk_path)], capture_output=True)
        logger.info(output)
        return True
    except AndroSignError:
        return False

def sign_apk(apk, v1=False, v2=True, keystore=None, key_alias=None, ks_pass=None, key_pass=None, out=None):
    apk_path = Path(apk)
    if not apk_path.exists():
        raise AndroSignError(f"APK not found: {apk_path}")

    tmpdir = tempfile.mkdtemp(prefix="androsing_")
    temp_apk = Path(tmpdir) / apk_path.name
    shutil.copy2(apk_path, temp_apk)

    try:
        if v2:
            temp_apk = Path(align_apk(temp_apk))
            sign_v2(temp_apk, keystore, key_alias, ks_pass, key_pass)

        if v1:
            sign_v1(temp_apk, keystore, key_alias, ks_pass, key_pass)

        if not verify(temp_apk):
            raise AndroSignError("Verification failed.")

        final_out = Path(out) if out else apk_path
        shutil.copy2(temp_apk, final_out)
        logger.info(f"Signed APK written to: {final_out}")
        return str(final_out)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
