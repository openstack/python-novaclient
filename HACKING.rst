Nova Client Style Commandments
==============================

- Step 1: Read the OpenStack Style Commandments
  http://docs.openstack.org/developer/hacking
- Step 2: Read on


Nova Client Specific Commandments
---------------------------------
None so far

Text encoding
-------------
- All text within python code should be of type 'unicode'.

    WRONG:

    >>> s = 'foo'
    >>> s
    'foo'
    >>> type(s)
    <type 'str'>

    RIGHT:

    >>> u = u'foo'
    >>> u
    u'foo'
    >>> type(u)
    <type 'unicode'>

- Transitions between internal unicode and external strings should always
  be immediately and explicitly encoded or decoded.

- All external text that is not explicitly encoded (database storage,
  commandline arguments, etc.) should be presumed to be encoded as utf-8.

    WRONG:

    mystring = infile.readline()
    myreturnstring = do_some_magic_with(mystring)
    outfile.write(myreturnstring)

    RIGHT:

    mystring = infile.readline()
    mytext = s.decode('utf-8')
    returntext = do_some_magic_with(mytext)
    returnstring = returntext.encode('utf-8')
    outfile.write(returnstring)

Running Tests
-------------
The testing system is based on a combination of tox and testr. If you just
want to run the whole suite, run `tox` and all will be fine. However, if
you'd like to dig in a bit more, you might want to learn some things about
testr itself. A basic walkthrough for OpenStack can be found at
http://wiki.openstack.org/testr
