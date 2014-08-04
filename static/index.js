var debug;

var _app = angular.module('_app', []);

_app.controller('_controller', ['$scope', '$http', function ($scope, $http) {
    $scope.settings = {
        defaultValues: [
            { name: 'orderByField', defaultValue: 'downloads' },
            { name: 'orderDescending', defaultValue: true },
            { name: 'displayNumSeeders', defaultValue: false },
            { name: 'displayNumLeechers', defaultValue: false },
            { name: 'displayNumDownloads', defaultValue: true },
            { name: 'displayNumGroupsPerDay', defaultValue: 15 },
            { name: 'downloadDaysPerRequest', defaultValue: 2 },
            { name: 'highlights', defaultValue: {} },
        ]
    };

    for (var index = 0; index < $scope.settings.defaultValues.length; index += 1) {
        var property = $scope.settings.defaultValues[index];
        $scope.settings.__defineGetter__(property.name, (function (property) {
            return function () {
                var value = localStorage.getItem(property.name);
                if (value != null && value != '') return JSON.parse(value);
                else return property.defaultValue;
            }
        })(property));
        $scope.settings.__defineSetter__(property.name, (function (property) {
            return function (value) {
                localStorage.setItem(property.name, JSON.stringify(value));
            }
        })(property));
    }

    $scope.days = [];
    
    $scope.pullTorrents = function (dayDelta) {
        var dayDelta = dayDelta || $scope.days.length;
        if (!$scope.days[dayDelta]) $scope.days[dayDelta] = { data: [], status: 'loading', expanded: false };
        $http.get('/torrents/' + dayDelta)
            .success(function (data, status, headers, config) {
                $scope.days[dayDelta].data = data.list;
                $scope.days[dayDelta].status = 'ok';
            })
            .error(function (data, status, headers, config) {
                $scope.days[dayDelta].staus = 'failed to load';
            });
    };
    
    for (var dayDelta = 0; dayDelta < 2; dayDelta += 1) {
        $scope.pullTorrents(dayDelta);
    }
    
    $scope.newHighlight = null;
    $scope.selectedHighlight = null;
    $scope.highlightsCache = null;
    
    $scope.deleteHighlight = function () {
        if ($scope.selectedHighlight != null) {
            var updatedHighlights = $scope.settings.highlights;
            delete updatedHighlights[$scope.selectedHighlight];
            $scope.settings.highlights = updatedHighlights;
            updateHighlightExpressions();
            $scope.selectedHighlight = null;
        }
    };
    
    $scope.createHighlight = function () {
        if ($scope.newHighlight != null) {
            var activeHighlights = $scope.settings.highlights,
                updatedHighlights = {};
            for (var key in activeHighlights)
                updatedHighlights[key] = activeHighlights[key];
            updatedHighlights[$scope.newHighlight] = { lastDownloadedEpisode: 0 };
            $scope.settings.highlights = updatedHighlights;
            updateHighlightExpressions();
            $scope.newHighlight = null;
        }
    };
    
    var updateHighlightExpressions = function () {
        $scope.highlightsCache = $scope.settings.highlights;
        $scope.highlightExpressions = {};
        for (var key in $scope.highlightsCache) {
            var tokens = key.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&"); // escaping RegExp special chars
            tokens = tokens.split(' ');
            var expression = [];
            for (var i = 0; i < tokens.length; i += 1)
                if (tokens[i]) expression.push('(' + tokens[i] + ')');
            if (expression.length > 0) {
                expression = '.*' + expression.join('.*') + '.*';
                expression = RegExp(expression, 'i');
                $scope.highlightExpressions[key] = expression;
            }
        }
    };

    updateHighlightExpressions();

    $scope.testAgainstHighlights = function (title, episode) {
        for (var key in $scope.highlightExpressions) {
            if ($scope.highlightExpressions[key].test(title)) {
                if (episode > $scope.settings.highlights[key].lastDownloadedEpisode) {
                    return key;
                }
            }
        }
        return false;
    };
    
    $scope.groupClick = function (title, episode) {
        var key = $scope.testAgainstHighlights(title, episode);
        if (key) {
            var highlights = $scope.settings.highlights;
            highlights[key].lastDownloadedEpisode = episode;
            $scope.highlightsCache = highlights;
            $scope.settings.highlights = highlights;
        }
    };

    debug = $scope;
}]);