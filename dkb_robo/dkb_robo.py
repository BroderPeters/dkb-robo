# pylint: disable=c0415, r0913
""" dkb internet banking automation library """
# -*- coding: utf-8 -*-
from dkb_robo.utilities import logger_setup, validate_dates, get_dateformat


LEGACY_DATE_FORMAT, API_DATE_FORMAT = get_dateformat()


class DKBRoboError(Exception):
    """ dkb-robo exception class """


class DKBRobo(object):
    """ dkb_robo class """
    # pylint: disable=R0904
    legacy_login = False
    dkb_user = None
    dkb_password = None
    proxies = {}
    last_login = None
    mfa_device = 0
    account_dic = {}
    tan_insert = False
    logger = None
    wrapper = None

    def __init__(self, dkb_user=None, dkb_password=None, tan_insert=False, legacy_login=False, debug=False, mfa_device=None):
        self.dkb_user = dkb_user
        self.dkb_password = dkb_password
        self.tan_insert = tan_insert
        self.legacy_login = legacy_login
        self.logger = logger_setup(debug)
        self.mfa_device = mfa_device

    def __enter__(self):
        """ Makes DKBRobo a Context Manager """
        # tan usage requires legacy login
        if self.tan_insert:
            self.legacy_login = True

        if self.mfa_device == 'm':
            self.mfa_device = 1

        if self.legacy_login:
            from dkb_robo.legacy import Wrapper
            self.wrapper = Wrapper(dkb_user=self.dkb_user, dkb_password=self.dkb_password, tan_insert=self.tan_insert, proxies=self.proxies, logger=self.logger)

        else:
            from dkb_robo.api import Wrapper
            self.wrapper = Wrapper(dkb_user=self.dkb_user, dkb_password=self.dkb_password, proxies=self.proxies, mfa_device=self.mfa_device, logger=self.logger)

        # login and get the account overview
        (self.account_dic, self.last_login) = self.wrapper.login()

        return self

    def __exit__(self, *args):
        """ Close the connection at the end of the context """
        self.wrapper.logout()

    def get_credit_limits(self):
        """ create a dictionary of credit limits of the different accounts """
        self.logger.debug('DKBRobo.get_credit_limits()\n')
        return self.wrapper.get_credit_limits()

    def get_exemption_order(self):
        """ get get_exemption_order """
        self.logger.debug('DKBRobo.get_exemption_order()\n')
        return self.wrapper.get_exemption_order()

    def get_points(self):
        """ returns the DKB points """
        self.logger.debug('DKBRobo.get_points()\n')
        return self.wrapper.get_points()

    def get_standing_orders(self, uid=None):
        """ get standing orders """
        self.logger.debug('DKBRobo.get_standing_orders()\n')
        return self.wrapper.get_standing_orders(uid)

    def get_transactions(self, transaction_url, atype, date_from, date_to, transaction_type='booked'):
        """ exported method to get transactions """
        self.logger.debug('DKBRobo.get_transactions(%s/%s: %s/%s)\n', transaction_url, atype, date_from, date_to)

        #if self.legacy_login:
        #    (date_from, date_to) = validate_dates(self.logger, date_from, date_to, 3, self.legacy_login)
        # else:
        (date_from, date_to) = validate_dates(self.logger, date_from, date_to, 3, self.legacy_login)

        transaction_list = self.wrapper.get_transactions(transaction_url, atype, date_from, date_to, transaction_type)

        self.logger.debug('DKBRobo.get_transactions(): %s transactions returned\n', len(transaction_list))
        return transaction_list

    def scan_postbox(self, path=None, download_all=False, archive=False, prepend_date=False):
        """ scan posbox and return document dictionary """
        self.logger.debug('DKBRobo.scan_postbox()\n')
        return self.wrapper.scan_postbox(path, download_all, archive, prepend_date)
