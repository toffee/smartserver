var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('printer', 'https://{{custom_printer_ip}}', 'user', 210, '{i18n_Laserprinter}', '{i18n_HPLaserJet}', "device_printer.svg", true);
subGroup.addUrl('gateway', 'https://{{default_server_gateway}}', 'admin', 220, '{i18n_Router}', '{i18n_FritzBox}', "device_wifi.svg", true);

subGroup = mx.Menu.getMainGroup('automation').getSubGroup('openhab');
subGroup.addUrl('basicui', ['user'], '//openhab.{host}/basicui/app', { 'order': 101, 'title': '{i18n_Homecontrol} Alt', 'info': '{i18n_Basic UI}', 'icon': 'openhab_basicui.svg', 'callbacks': { 'ping': mx.OpenHAB.applyTheme } });
