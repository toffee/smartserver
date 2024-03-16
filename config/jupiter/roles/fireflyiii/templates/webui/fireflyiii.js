var subGroup = mx.Menu.getMainGroup('workspace').addSubGroup('financial', { 'order': 180, 'title': '{i18n_Financial}', 'icon': 'financial_logo.svg' });
subGroup.addUrl('fireflyiii', ['user'], '//fireflyiii.{host}/', { 'order': 181, 'title': '{i18n_FireflyIII}', 'info': '{i18n_FireflyIII}', 'icon': "fireflyiii_logo.svg", 'target': '_blank'});
subGroup.addUrl('fireflyiii_importer', ['user'], '/fireflyiii-importer/', { 'order': 182, 'title': '{i18n_FireflyIII Importer}', 'info': '{i18n_FireflyIII Importer}', 'icon': "fireflyiii_logo.svg", 'target': '_blank'});

