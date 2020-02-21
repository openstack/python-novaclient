Nova Client Style Commandments
==============================

- Step 1: Read the OpenStack Style Commandments
  https://docs.openstack.org/hacking/latest
- Step 2: Read on

Nova Client Specific Commandments
---------------------------------
None so far

Text encoding
-------------

- Transitions between internal unicode and external strings should always
  be immediately and explicitly encoded or decoded.

- All external text that is not explicitly encoded (database storage,
  commandline arguments, etc.) should be presumed to be encoded as utf-8.

  Wrong::

    mystring = infile.readline()
    myreturnstring = do_some_magic_with(mystring)
    outfile.write(myreturnstring)

  Right::

    mystring = infile.readline()
    mytext = s.decode('utf-8')
    returntext = do_some_magic_with(mytext)
    returnstring = returntext.encode('utf-8')
    outfile.write(returnstring)

Running Tests
-------------

The testing system is based on a combination of tox and stestr. If you just
want to run the whole suite, run ``tox`` and all will be fine. However, if
you'd like to dig in a bit more, you might want to learn some things about
stestr itself.
