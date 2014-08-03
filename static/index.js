var debug;

var _app = angular.module('_app', []);

_app.controller('_controller', ['$scope', '$http', function ($scope, $http) {
    $scope.strings = {
        displayNumGroupsPerDayHelp: 'Maximum number of groups to display in a single day.',
    };

    function CustomBooleanIn(value) { return !!value ? '1' : '0'; }
    function CustomBooleanOut(value) { return !!Number(value); }
    function CustomArrayIn(array) { return array.join('^_^'); }
    function CustomArrayOut(string) { return string.length ? string.split('^_^') : []; }

    $scope.settings = {
        defaultValues: [
            { name: 'orderByField', defaultValue: 'downloads', castIn: String, castOut: String },
            { name: 'orderDescending', defaultValue: true, castIn: CustomBooleanIn, castOut: CustomBooleanOut },
            { name: 'displayNumSeeders', defaultValue: false, castIn: CustomBooleanIn, castOut: CustomBooleanOut },
            { name: 'displayNumLeechers', defaultValue: false, castIn: CustomBooleanIn, castOut: CustomBooleanOut },
            { name: 'displayNumDownloads', defaultValue: true, castIn: CustomBooleanIn, castOut: CustomBooleanOut },
            { name: 'displayNumGroupsPerDay', defaultValue: 15, castIn: String, castOut: Number },
            { name: 'downloadDaysPerRequest', defaultValue: 2, castIn: String, castOut: Number },
            { name: 'highlights', defaultValue: ['debug'], castIn: CustomArrayIn, castOut: CustomArrayOut },
        ]
    };

    for (var index = 0; index < $scope.settings.defaultValues.length; index += 1) {
        var property = $scope.settings.defaultValues[index];
        $scope.settings.__defineGetter__(property.name, (function (property) {
            return function () {
                var value = localStorage.getItem(property.name);
                if (value != null) return property.castOut(localStorage.getItem(property.name));
                else return property.defaultValue;
            }
        })(property));
        $scope.settings.__defineSetter__(property.name, (function (property) {
            return function (value) { localStorage.setItem(property.name, property.castIn(value)); }
        })(property));
    }

    $scope.days = [];
    
    $scope.pullTorrents = function (dayDelta) {
        var dayDelta = dayDelta || $scope.days.length;
        if (!$scope.days[dayDelta]) $scope.days[dayDelta] = { data: [] };
        $scope.days[dayDelta].loading = true;
        $scope.days[dayDelta].failedToLoad = false;
        $http.get('/torrents/' + dayDelta)
            .success(function (data, status, headers, config) {
                $scope.days[dayDelta].data = data.list;
                $scope.days[dayDelta].loading = false;
            })
            .error(function (data, status, headers, config) {
                console.log(data, status, headers, config);
                $scope.days[dayDelta].failedToLoad = true;
                $scope.days[dayDelta].loading = false;
            });
    };
    
    for (var dayDelta = 0; dayDelta < 2; dayDelta += 1) {
        $scope.pullTorrents(dayDelta);
    }
    
    $scope.newHighlight = null;
    $scope.selectedHighlight = null;
    
    $scope.deleteSelectedHighlight = function () {
        var shl = $scope.selectedHighlight,
            ahl = $scope.settings.highlights;
        if (shl != null) {
            var idx = ahl.indexOf(shl);
            $scope.settings.highlights = ahl.slice(0, idx).concat(ahl.slice(idx + 1));
            updateHighlightExpressions();
        }
        $scope.selectedHighlight = null;
    };
    
    $scope.createHighlight = function () {
        if ($scope.newHighlight != null) {
            var highlight = $scope.newHighlight.trim();
            if (highlight) {
                $scope.settings.highlights = $scope.settings.highlights.concat(highlight);
            }
            $scope.newHighlight = null;
            updateHighlightExpressions();
        }
    };
    
    var updateHighlightExpressions = function () {
        $scope.highlightExpressions = [];
        for (var index in $scope.settings.highlights) {
            var tokens = $scope.settings.highlights[index];
            tokens = tokens.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
            tokens = tokens.split(' ');
            var expression = [];
            for (var i = 0; i < tokens.length; i += 1)
                if (tokens[i]) expression.push('(' + tokens[i] + ')');
            if (expression.length > 0) {
                expression = '.*' + expression.join('.*') + '.*';
                expression = RegExp(expression, 'i');
                $scope.highlightExpressions.push(expression);
            }
        }
    };

    updateHighlightExpressions();

    $scope.testAgainstHighlights = function (title) {
        for (var index in $scope.highlightExpressions) {
            if ($scope.highlightExpressions[index].test(title))
                return true;
        }
        return false;
    };

    debug = $scope;
}]);