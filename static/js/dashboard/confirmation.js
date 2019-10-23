$('[data-toggle=confirmation]').confirmation(
    {rootSelector: '[data-toggle=confirmation]'
        , singleton: true
        , popout: true, content: 'Do you want to continue?'});