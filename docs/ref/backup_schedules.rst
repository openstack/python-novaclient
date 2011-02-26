Backup schedules
================

.. currentmodule:: novaclient

Rackspace allows scheduling of weekly and/or daily backups for virtual
servers. You can access these backup schedules either off the API object as
:attr:`OpenStack.backup_schedules`, or directly off a particular
:class:`Server` instance as :attr:`Server.backup_schedule`.

Classes
-------

.. autoclass:: BackupScheduleManager
   :members: create, delete, update, get
   
.. autoclass:: BackupSchedule
   :members: update, delete
   
   .. attribute:: enabled
   
        Is this backup enabled? (boolean)
        
   .. attribute:: weekly
   
        The day of week upon which to perform a weekly backup.
   
   .. attribute:: daily
   
        The daily time period during which to perform a daily backup.
        
Constants
---------

Constants for selecting weekly backup days:

    .. data:: BACKUP_WEEKLY_DISABLED
    .. data:: BACKUP_WEEKLY_SUNDAY
    .. data:: BACKUP_WEEKLY_MONDAY  
    .. data:: BACKUP_WEEKLY_TUESDAY 
    .. data:: BACKUP_WEEKLY_WEDNESDA
    .. data:: BACKUP_WEEKLY_THURSDAY
    .. data:: BACKUP_WEEKLY_FRIDAY  
    .. data:: BACKUP_WEEKLY_SATURDAY
    
Constants for selecting hourly backup windows:

    .. data:: BACKUP_DAILY_DISABLED   
    .. data:: BACKUP_DAILY_H_0000_0200
    .. data:: BACKUP_DAILY_H_0200_0400
    .. data:: BACKUP_DAILY_H_0400_0600
    .. data:: BACKUP_DAILY_H_0600_0800
    .. data:: BACKUP_DAILY_H_0800_1000
    .. data:: BACKUP_DAILY_H_1000_1200
    .. data:: BACKUP_DAILY_H_1200_1400
    .. data:: BACKUP_DAILY_H_1400_1600
    .. data:: BACKUP_DAILY_H_1600_1800
    .. data:: BACKUP_DAILY_H_1800_2000
    .. data:: BACKUP_DAILY_H_2000_2200
    .. data:: BACKUP_DAILY_H_2200_0000
