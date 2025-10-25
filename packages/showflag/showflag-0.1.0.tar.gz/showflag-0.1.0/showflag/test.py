import os, pty, select, re, sys, time, errno, fcntl

FLAG = "/flag"

def nb(fd):
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

def read_until(fd, timeout=2.0, stop_tokens=(b'=', b'?', b'Answer', b'answer')):
    end = time.time() + timeout
    buf = b""
    while time.time() < end:
        r,_,_ = select.select([fd], [], [], max(0, end-time.time()))
        if not r:
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError as e:
            if e.errno in (errno.EIO, errno.EBADF):
                break
            raise
        if not chunk:
            break
        buf += chunk
        if any(tok in buf for tok in stop_tokens):
            break
    return buf

def compute(expr_text: str):
    # 1) 숫자 3개 a*b+c 시도
    nums = re.findall(r'-?\d+', expr_text)
    if len(nums) >= 3:
        a,b,c = map(int, nums[:3])
        return a*b + c
    # 2) '=' 또는 '?' 앞의 식만 추출하여 안전 문자만 남기고 eval
    m = re.search(r'^(.*?)[=\?]', expr_text, flags=re.S)
    expr = (m.group(1) if m else expr_text).strip()
    expr = re.sub(r'[^0-9\+\-\*\/%\(\)\s\.]', '', expr)
    if not expr:
        return None
    # eval은 안전 문자만 허용된 상태에서만 사용 (연산만)
    try:
        val = eval(expr, {"__builtins__":None}, {})
    except Exception:
        return None
    try:
        return int(val)
    except Exception:
        return val

def main():
    try:
        pid, mfd = pty.fork()
    except Exception as e:
        print("ERROR: PTY fork failed:", e, file=sys.stderr)
        return 1

    if pid == 0:
        # child: exec /flag
        try:
            os.execv(FLAG, [FLAG])
        except Exception as e:
            print("exec failed:", e, file=sys.stderr)
            os._exit(127)

    # parent: talk via master fd
    nb(mfd)

    # 0) 몇몇 바이너리는 엔터를 먼저 받아야 프롬프트가 뜸 → 웨이크업
    try:
        os.write(mfd, b"\n")
        time.sleep(0.05)
        os.write(mfd, b"\n")
    except Exception:
        pass

    # 1) 프롬프트 읽기
    out1 = read_until(mfd, timeout=3.0)
    # 프롬프트가 안 뜨면 추가로 더 읽기/깨우기
    if not out1.strip():
        try:
            os.write(mfd, b"\n")
        except Exception:
            pass
        out1 += read_until(mfd, timeout=2.0)

    text1 = out1.decode('utf-8', errors='replace')

    # 2) 수식 계산
    ans = compute(text1)
    if ans is None:
        # 마지막 시도: 숫자 3개로 강제
        nums = re.findall(r'-?\d+', text1)
        if len(nums) >= 3:
            a,b,c = map(int, nums[:3])
            ans = a*b + c

    if ans is None:
        # 디버그 출력 후 종료
        print(text1.strip())
        print("ERROR: cannot parse expression.", file=sys.stderr)
        return 2

    # 3) 정답 전송
    try:
        os.write(mfd, (str(ans) + "\n").encode())
    except Exception as e:
        print("ERROR: write answer failed:", e, file=sys.stderr)
        return 3

    # 4) 나머지 출력 수집 (플래그)
    out2 = read_until(mfd, timeout=2.0, stop_tokens=())  # EOF/timeout까지
    # 조금 더 기다려 잔여 출력 수집
    out2 += read_until(mfd, timeout=1.0, stop_tokens=())
    full = (text1 + out2.decode('utf-8', errors='replace')).strip()

    # 5) 플래그만 뽑아 출력(없으면 전체 출력)
    m = re.search(r'\b[A-Za-z0-9_\-]*\{.*?\}', full)
    print(m.group(0) if m else full)

    # 종료 처리
    try:
        os.close(mfd)
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(main())