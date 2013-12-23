def f():
    try:
        print 'try 1'
        1/0
        print 'try 2'
    except Exception:
        print 'except'
    finally:
        print 'finally'

f()