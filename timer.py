import re
import sys
import time
from datetime import datetime, timedelta

def parse_timer(expr):
    expr = expr.strip()
    expr = expr.strip('{}').replace(' ', '')
    
    # handle comma-separated work/break timers
    if ',' in expr:
        work, break_ = expr.split(',')
        work_timers = _parse_math(work)
        break_timers = _parse_math(break_)
        
        # interleave work and break timers
        timers = []
        for w, b in zip(work_timers, break_timers + [break_timers[-1]]*(len(work_timers)-len(break_timers))):
            timers.append(w)
            timers.append(b)
        return timers
    else:
        return _parse_math(expr)

def _parse_math(expr):
    
    # multiplication and subtraction
    if 'x' in expr:
        parts = expr.split('x')
        nums = []
        for p in parts:
            if '-' in p:
                base, sub = map(int, p.split('-'))
                nums.append(base)
                nums.append(-sub)
            else:
                nums.append(int(p))
                
        # if subtraction is at the end
        if '-' in parts[-1]:
            base, sub = map(int, parts[-1].split('-'))
            nums[-1] = base
            subtract = sub
        else:
            subtract = 0
            
        # calculate sequence
        timers = []
        val = nums[0]
        reps = nums[1] if len(nums) > 1 else 1
        mult = nums[2] if len(nums) > 2 else 1
        for i in range(reps):
            timers.append(val * mult - subtract * i)
        return timers
    elif '-' in expr:
        nums = list(map(int, expr.split('-')))
        return nums
    elif re.match(r'^\d+$', expr):
        return [int(expr)]
    else:
        raise ValueError("invalid timer expression")

def format_time(secs):
    mins, secs = divmod(secs, 60)
    return f"{mins:02}:{secs:02}"

def run_timer(timers, expr):
    for idx, t in enumerate(timers):
        print(f"timer {idx+1}/{len(timers)}: {t} minutes")
        end_time = datetime.now() + timedelta(minutes=t)
        while True:
            now = datetime.now()
            remaining = (end_time - now).total_seconds()
            if remaining <= 0:
                sys.stdout.write("\r" + " " * 30 + "\r")  # clear line
                print("time's up!")
                break
            sys.stdout.write(f"\rtimer {format_time(int(remaining))}")
            sys.stdout.flush()
            time.sleep(1)
            
            # non-blocking input (linux only)
            import select
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                inp = sys.stdin.readline().strip()
                if inp == 'q':
                    print("\nquitting.")
                    return
                elif inp == 'r':
                    print("\nrestarting current timer")
                    end_time = datetime.now() + timedelta(minutes=t)
                elif inp == '\x12':  # ctrl-R
                    print("\nrestarting all timers")
                    run_timer(timers, expr)
                    return
        print()

def main():
    print("mmvii")
    expr = input().strip()
    if expr.startswith('{') and expr.endswith('}'):
        expr_display = expr
    else:
        expr_display = f"{{ {expr} }}"
    try:
        timers = parse_timer(expr)
    except Exception as e:
        print(f"Error: {e}")
        return
        
    sys_time = datetime.now().strftime('%H:%M:%S')
    start_time = datetime.now().strftime('%H:%M:%S')
    end_time = (datetime.now() + timedelta(minutes=sum(timers))).strftime('%H:%M:%S')
    print(f"sys    {sys_time}")
    print(f"start  {start_time}")
    print(f"end    {end_time}")
    print(f"      {expr_display}")
    run_timer(timers, expr_display)

if __name__ == "__main__":
    main()
