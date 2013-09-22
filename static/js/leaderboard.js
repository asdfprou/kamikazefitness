var leaderboardApp = angular.module('leaderboard', []);

leaderboardApp.controller('LBoardCtrl', function LBoardCtrl ($scope, $http) {
    // helper for formatting date
    var humanReadableDate = function (d) {
        return d.getUTCMonth() + '/' + d.getUTCDate();
    };)})

    var users = db.users.find({});

    console.log(users);

    $scope.getUsers = function () {
        $http({
            method: 'GET',
            url: '/user/findAll'
        }).
        success(function (data) {
            $scope.users = JSON.parse(data);
            $scope.error = '';
        }).
        error(function (data, status) {
            if (status === 404) {
                $scope.error = 'No users to be found here!';
            } else {
                $scope.error = 'Error: ' + status;
            }
        })
    }

    $scope.getUsers();
}

leaderboardApp.directive('ghVisualization', function ($scope) {
    var margin = { top: 50, right: 0, bottom: 100, left: 30 },
      width = 960 - margin.left - margin.right,
      height = 430 - margin.top - margin.bottom,
      gridSize = Math.floor(width / 24),
      legendElementWidth = gridSize*2,
      buckets = 9,
      colors = ["#EC6363","#BDEBCA"], // or ex: colorbrewer.YlGnBu[9]
      days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
      users = $scope.users;


    var render = function (data) {
      var colorScale = d3.scale.quantile()
          .domain([0, buckets - 1, d3.max(data, function (d) { return d.value; })])
          .range(colors);

      var svg = d3.select("#leaderboard").append("svg")
          .attr("width", width + margin.left + margin.right)
          .attr("height", height + margin.top + margin.bottom)
          .append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

      var dayLabels = svg.selectAll(".dayLabel")
          .data(days)
          .enter().append("text")
            .text(function (d) { return d; })
            .attr("x", 0)
            .attr("y", function (d, i) { return i * gridSize; })
            .style("text-anchor", "end")
            .attr("transform", "translate(-6," + gridSize / 1.5 + ")")
            .attr("class", function (d, i) { return ((i >= 0 && i <= 4) ? "dayLabel mono axis axis-workweek" : "dayLabel mono axis"); });

      var userLabels = svg.selectAll(".userLabel")
          .data(times)
          .enter().append("text")
            .text(function(d) { return d; })
            .attr("x", function(d, i) { return i * gridSize; })
            .attr("y", 0)
            .style("text-anchor", "middle")
            .attr("transform", "translate(" + gridSize / 2 + ", -6)")
            .attr("class", function(d, i) { return ((i >= 7 && i <= 16) ? "userLabel mono axis axis-worktime" : "userLabel mono axis"); });

      var heatMap = svg.selectAll(".active")
          .data(data)
          .enter().append("rect")
          .attr("x", function(d) { return (d.hour - 1) * gridSize; })
          .attr("y", function(d) { return (d.day - 1) * gridSize; })
          .attr("rx", 4)
          .attr("ry", 4)
          .attr("class", "active bordered")
          .attr("width", gridSize)
          .attr("height", gridSize)
          .style("fill", colors[0]);

      heatMap.transition().duration(1000)
          .style("fill", function(d) { return colorScale(d.value); });

      heatMap.append("title").text(function(d) { return d.value; });

      var legend = svg.selectAll(".legend")
          .data([0].concat(colorScale.quantiles()), function(d) { return d; })
          .enter().append("g")
          .attr("class", "legend");

      legend.append("rect")
        .attr("x", function(d, i) { return legendElementWidth * i; })
        .attr("y", height)
        .attr("width", legendElementWidth)
        .attr("height", gridSize / 2)
        .style("fill", function(d, i) { return colors[i]; });

      legend.append("text")
        .attr("class", "mono")
        .text(function(d) { return "≥ " + Math.round(d); })
        .attr("x", function(d, i) { return legendElementWidth * i; })
        .attr("y", height + gridSize);
    }

    render($scope.data);
});
