def func(input):
    valid=True
    try:
        try:
            if input=='error':
                print "raise"
                raise Exception
        except:
            print "except"
            valid=False
            raise TypeError
        finally:
            print "finally"
            return valid
    except:
        print "except 2"
    print "exit normally"
    return valid

def func2(input):
    try:
        a=func(input)
    except Exception as e:
        print 'except func2'+repr(e)
    print a