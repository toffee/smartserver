var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('gateway', 'https://{{default_server_gateway}}', 'admin', 220, '{i18n_Router}', '{i18n_FritzBox}', "device_wifi.svg", true);
subGroup.addUrl('router', 'http://{{terminus_ip}}', 'admin', 230, '{i18n_Terminus}', '{i18n_Terminus}', 'router.svg', true);
subGroup.addUrl('switch', 'https://{{switch_ip}}', 'admin', 241, '{i18n_Switch}', '{i18n_Switch}', 'switch.svg', true);
