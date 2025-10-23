""" ae_sys_core unit tests """
import pytest

from configparser import ConfigParser

from ae.base import CFG_EXT
from ae.core import DEBUG_LEVEL_DISABLED, DEBUG_LEVEL_ENABLED, DEBUG_LEVEL_VERBOSE
from ae.console import ConsoleApp

from ae.sys_core import SystemBase, SystemConnectorBase, UsedSystems


SS = 'Ss'                               # test system ids; change together with related config var in test.cfg
SX = 'Xx'
SY = 'Yy'

USR_CFG = 'cfg_user_ss'                 # change together with related config var in test.cfg
PWD_CFG = 'cfg_secret'                  # change together with related config var in test.cfg

CRED_KEY_USR = 'User'
CRED_KEY_PWD = 'Password'
USR_NAME1 = 'test_user'
ALL_CREDENTIALS = {SS.lower() + CRED_KEY_USR: USR_NAME1,
                   SX.lower() + CRED_KEY_USR: USR_NAME1,
                   SY.lower() + CRED_KEY_USR: USR_NAME1}
SYS_CREDENTIALS = {CRED_KEY_USR: USR_NAME1}
FEATURE1 = 'ss_extra_feature'
SYS_FEATURES = [FEATURE1]
SYS_DICTS = {SS: {'connector_module': 'sys_core_test_mocks', 'connector_class': 'connector_success_mock'},
             SX: {'connector_module': 'sys_core_test_mocks', 'connector_class': 'connector_failure_mock'},
             SY: {'connector_module': 'sys_core_test_mocks', 'connector_class': 'disconnect_failure_mock'}
             }


@pytest.fixture
def console_app_env(restore_app_env):
    """ ConsoleApp with automatic option, sys.argv reset and app unregister. """
    yield ConsoleApp('Console App Environment for ae.sys_core tests', additional_cfg_files=("tests/test" + CFG_EXT, ))


class TestConfig:
    """ using the config test file test.cfg """
    def test_available(self, console_app_env):
        us = UsedSystems(console_app_env)
        assert SS in us
        assert SX in us
        assert SY in us
        assert {k: v['name'] for k, v in us.available_systems.items()} \
            == {'Ss': 'System S', 'Xx': 'SystemX', 'Yy': 'SysY'}
        assert us[SY].available_rec_types == {'C': 'Clients', 'R': 'Reservations', 'P': 'Products'}

    def test_credentials(self, console_app_env):
        us = UsedSystems(console_app_env)
        assert us[SS].credentials == {'User': 'cfg_user_ss', 'Password': PWD_CFG}
        assert us[SX].credentials == {'User': 'cfg_user_xx'}
        assert us[SY].credentials == {'User': 'cfg_user_yy'}

    def test_features(self, console_app_env):
        us = UsedSystems(console_app_env)
        assert us[SS].features == ["Feature=feature_ss"]
        assert us[SX].features == ["Feature=feature_xx"]
        assert us[SY].features == ["Feature=feature_yy"]


class TestSystemBase:
    def test_init_empty_cred(self, console_app_env):
        empty_dict = {}
        s = SystemBase(SX, console_app_env, empty_dict)
        assert s.sys_id == SX
        assert s.credentials == empty_dict
        assert s.features == ()
        assert s.connection is None
        assert s.conn_error == ''

    def test_init_entered_cred(self, console_app_env):
        user_cred = dict(User='test_usr_name')
        feat = ('WhatAFeature', )
        s = SystemBase(SX, console_app_env, user_cred, feat)
        assert s.sys_id == SX
        assert s.credentials == user_cred
        assert s.features == feat
        assert s.connection is None
        assert s.conn_error == ''

    def test_repr_debug_enabled(self, console_app_env):
        ext_cred = SYS_CREDENTIALS.copy()
        ext_cred[CRED_KEY_PWD] = 's_e_c_r_e_t'
        s = SystemBase(SS, console_app_env, ext_cred, features=SYS_FEATURES)
        usr = s.credentials.get(CRED_KEY_USR)
        pwd = s.credentials.get(CRED_KEY_PWD)

        console_app_env.debug_level = DEBUG_LEVEL_DISABLED
        assert SS in repr(s)
        assert usr not in repr(s)
        assert pwd not in repr(s)
        assert FEATURE1 not in repr(s)
        assert console_app_env.app_name not in repr(s)

        console_app_env.debug_level = DEBUG_LEVEL_ENABLED
        assert SS in repr(s)
        assert usr in repr(s)
        assert pwd not in repr(s)
        assert FEATURE1 in repr(s)
        assert console_app_env.app_name in repr(s)

    def test_repr_debug_verbose(self, console_app_env):
        s = SystemBase(SS, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        s.console_app.debug_level = DEBUG_LEVEL_VERBOSE
        usr = s.credentials.get(CRED_KEY_USR)
        assert SS in repr(s)
        assert usr in repr(s)
        assert FEATURE1 in repr(s)
        assert repr(s.features) in repr(s)
        assert console_app_env.app_name in repr(s)

    def test_repr_debug_verbose_pwd(self, console_app_env):
        ext_cred = SYS_CREDENTIALS.copy()
        ext_cred[CRED_KEY_PWD] = 's_e_c_r_e_t'
        s = SystemBase(SS, console_app_env, ext_cred, features=SYS_FEATURES)
        usr = s.credentials.get(CRED_KEY_USR)
        pwd = s.credentials.get(CRED_KEY_PWD)

        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        assert SS in repr(s)
        assert usr in repr(s)
        assert pwd in repr(s)
        assert FEATURE1 in repr(s)
        assert console_app_env.app_name in repr(s)

    def test_repr_after_error(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        s = SystemBase(SX, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        assert SX in repr(s)
        assert s.connect(SYS_DICTS[SX]) == 'ConnectError'
        assert s.conn_error == 'ConnectError'
        assert s.conn_error in repr(s)

    def test_connect_and_close(self, console_app_env):
        s = SystemBase(SS, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        assert s.connect(SYS_DICTS[SS]) == ''
        assert hasattr(s.connection, 'connect')
        assert s.conn_error == ''
        assert s.disconnect() == ''
        assert s.conn_error == ''

    def test_connect_error(self, console_app_env):
        s = SystemBase(SX, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        assert s.connect(SYS_DICTS[SX]) == 'ConnectError'
        assert not hasattr(s.connection, 'connect')
        assert s.conn_error == 'ConnectError'
        assert s.disconnect() == ''
        assert s.conn_error == ''

        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        s = SystemBase(SX, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        assert s.connect(SYS_DICTS[SX]) == 'ConnectError'
        assert s.conn_error == 'ConnectError'
        assert s.disconnect() == ''
        assert s.conn_error == ''

    def test_close_error(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        s = SystemBase(SY, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        assert s.connect(SYS_DICTS[SY]) == ''
        assert hasattr(s.connection, 'disconnect')
        s.connection.disconnect = None
        assert s.conn_error == ''
        assert s.disconnect() == 'CloseError'
        assert s.conn_error == 'CloseError'

    def test_disconnect_error(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        s = SystemBase(SY, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        assert s.connect(SYS_DICTS[SY]) == ''
        assert hasattr(s.connection, 'close')
        s.connection.close = None
        assert s.disconnect() == 'DisconnectError'
        assert s.conn_error == 'DisconnectError'


class SystemConn(SystemConnectorBase):
    """ basic stub implementation of abstract base class """
    def connect(self) -> str:
        """ mock/dummy connect """
        return self.last_err_msg


class TestSystemConnectionBase:
    def test_init(self, console_app_env):
        empty_dict = {}
        s = SystemBase(SX, console_app_env, empty_dict)
        with pytest.raises(TypeError):
            # noinspection PyAbstractClass
            SystemConnectorBase(s)

        sc = SystemConn(s)
        assert sc.system is s
        assert sc.console_app is console_app_env
        assert sc.last_err_msg == ""
        assert sc.system.credentials is empty_dict

    def test_repr_debug_change(self, console_app_env):
        ext_cred = SYS_CREDENTIALS.copy()
        ext_cred[CRED_KEY_PWD] = 's_e_c_r_e_t'
        s = SystemBase(SS, console_app_env, ext_cred, features=SYS_FEATURES)
        sc = SystemConn(s)
        usr = sc.system.credentials.get(CRED_KEY_USR)
        pwd = sc.system.credentials.get(CRED_KEY_PWD)
        console_app_env.debug_level = DEBUG_LEVEL_DISABLED

        assert SS in repr(sc)
        assert usr not in repr(sc)
        assert pwd not in repr(sc)
        assert FEATURE1 not in repr(sc)
        assert console_app_env.app_name not in repr(sc)

    def test_connect(self, console_app_env):
        empty_dict = {}
        s = SystemBase(SX, console_app_env, empty_dict)
        sc = SystemConn(s)
        assert sc.connect() == ""

    def test_repr_debug_verbose(self, console_app_env):
        s = SystemBase(SS, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        s.console_app.debug_level = DEBUG_LEVEL_VERBOSE
        sc = SystemConn(s)
        usr = sc.system.credentials.get(CRED_KEY_USR)
        assert SS in repr(sc)
        assert usr in repr(sc)
        assert FEATURE1 in repr(sc)
        assert repr(s.features) in repr(sc)
        assert console_app_env.app_name in repr(sc)

    def test_repr_after_error(self, console_app_env):
        s = SystemBase(SX, console_app_env, SYS_CREDENTIALS, features=SYS_FEATURES)
        sc = SystemConn(s)
        tem = "TestErrorMessage"
        sc.last_err_msg = tem
        assert SX in repr(sc)
        assert sc.last_err_msg == tem
        assert tem in repr(sc)


class TestUsedSystems:
    def test_init_from_cfg(self, console_app_env):
        us = UsedSystems(console_app_env)
        assert SS in us.available_systems and SX in us.available_systems and SY in us.available_systems
        assert SS in us and SX in us and SY in us
        assert us[SS].credentials[CRED_KEY_USR] == USR_CFG
        assert us[SS].credentials[CRED_KEY_PWD] == PWD_CFG

    def test_init_selected_all(self, console_app_env):
        us = UsedSystems(console_app_env, SS, SX, SY)
        assert SS in us.available_systems and SX in us.available_systems and SY in us.available_systems
        assert SS in us and SX in us and SY in us
        assert us[SS].credentials[CRED_KEY_USR] == USR_CFG
        assert us[SS].credentials[CRED_KEY_PWD] == PWD_CFG

    def test_init_selected_one_and_verbose(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        us = UsedSystems(console_app_env, SS, **ALL_CREDENTIALS)
        assert SS in us.available_systems
        assert SX not in us.available_systems
        assert SY not in us.available_systems
        assert SS in us and SX not in us and SY not in us
        assert us[SS].credentials[CRED_KEY_USR] == USR_NAME1
        assert us[SS].credentials[CRED_KEY_PWD] == PWD_CFG
        assert PWD_CFG in repr(us)      # password is visible because of DEBUG_LEVEL_VERBOSE

    def test_init_missing_cfg(self, console_app_env):
        print("POPPED", console_app_env._cfg_files.pop(-1))  # remove tests/test.cfg and reset ConfigParser for coverage
        console_app_env._cfg_parser = ConfigParser()
        console_app_env.load_cfg_files()
        us = UsedSystems(console_app_env)
        assert getattr(us, 'available_systems', None) is None

    def test_init_missing_cred(self, console_app_env):
        us = UsedSystems(console_app_env)
        us.available_systems[SS]['credential_keys'] += ('MissingCredentialKey', )
        us.clear()
        us._load_merge_cred_feat({})
        assert SS not in us

    def test_init_hidden_password(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_ENABLED
        us = UsedSystems(console_app_env)
        assert us[SS].credentials[CRED_KEY_PWD] == PWD_CFG
        assert PWD_CFG not in repr(us)

    def test_connect_and_close_sys(self, console_app_env):
        us = UsedSystems(console_app_env, SS, **ALL_CREDENTIALS)
        us.available_systems[SS].update(SYS_DICTS[SS])
        assert us.connect() == ''
        assert us.disconnect() == ''

    def test_connect_and_close_debug(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        us = UsedSystems(console_app_env, SS, **ALL_CREDENTIALS)
        us.available_systems[SS].update(SYS_DICTS[SS])
        assert us.connect() == ''
        assert us.disconnect() == ''

    def test_connect_and_close_conn_err(self, console_app_env):
        us = UsedSystems(console_app_env, SX, **ALL_CREDENTIALS)
        us.available_systems[SX].update(SYS_DICTS[SX])
        assert 'ConnectError' in us.connect()
        assert us.disconnect() == ''

    def test_connect_and_close_conn_err_debug(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        us = UsedSystems(console_app_env, SX, **ALL_CREDENTIALS)
        us.available_systems[SX].update(SYS_DICTS[SX])
        assert 'ConnectError' in us.connect()
        assert us.disconnect() == ''

    def test_connect_and_disconnect_err(self, console_app_env):
        us = UsedSystems(console_app_env, SY, **ALL_CREDENTIALS)
        us.available_systems[SY].update(SYS_DICTS[SY])
        assert us.connect() == ''
        assert 'DisconnectError' in us.disconnect()

    def test_connect_and_close_err(self, console_app_env):
        console_app_env.debug_level = DEBUG_LEVEL_VERBOSE
        us = UsedSystems(console_app_env, SY, **ALL_CREDENTIALS)
        us.available_systems[SY].update(SYS_DICTS[SY])
        assert us.connect() == ''
        us[SY].connection.disconnect = None
        assert 'CloseError' in us.disconnect()
