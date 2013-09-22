var leaderboardApp = angular.module('leaderboard', ['angular-underscore/filters', 'angularMoment', 'd3']);

leaderboardApp.controller('LBoardCtrl', function LBoardCtrl($scope, $http) {
    // helper for formatting date
    $scope.getUsers = function (cb) {
        $http({
            method: 'GET',
            url: '/user'
        }).
        success(function (data) {
            $scope.users = _.pluck(JSON.parse(data), 'name');
            $scope.error = '';
            cb($scope.users, $http);
        }).
        error(function (data, status) {
            if (status === 404) {
                $scope.error = 'No users to be found here!';
            } else {
                $scope.error = 'Error: ' + status;
            }
        })
    }

    $scope.getUsers(function (users, $http) {
        $http({
            method: 'GET',
            url: '/activity'
        }).
        success(function (data) {
          $scope.data(data);
        }).
        error(function (data, status) {
            if (status === 404) {
                $scope.error = 'No activities to be found here!';
            } else {
                $scope.error = 'Error: ' + status;
            }
        })
    });
});

leaderboardApp.directive('ghVisualization', function ($scope) {
  d3.json("static/js/data.json", function(error, json) {
    var margin = { top: 50, right: 0, bottom: 150, left: 30 },
      width = 400 - margin.left - margin.right,
      height = 600 - margin.top - margin.bottom,
      users = ['user1', 'user2', 'user3', 'user4', 'user5', 'user6', 'user7'],
      days = ["Sa", "Su", "Mo", "Tu", "We", "Th", "Fr"],
      gridSize = Math.floor(width / users.length),
      legendElementWidth = gridSize,
      colors = ["#D0CCC0", "#DFD487","#EC6363","#BDEBCA"]; // or ex: colorbrewer.YlGnBu[9]
      
      //users = $scope.users;
      //data = $scope.data;
    var data = json;

    var activityScale = d3.scale.ordinal()
        .domain(["filler","na", "active", "inactive"])
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
          .attr("transform", "translate(-6," + gridSize / 2 + ")")
          .attr("class", "dayLabel mono axis");

    var userLabels = svg.selectAll(".userLabel")
        .data(users)
        .enter().append("text")
          .text(function(d) { return d; })
          .attr("x", function(d, i) { return i * gridSize; })
          .attr("y", 0)
          .style("text-anchor", "middle")
          .attr("transform", "translate(" + gridSize / 2 + ", -6)")
          .attr("class", "userLabel mono axis");

    var heatMap = svg.selectAll(".activity")
        .data(data)
        .enter().append("rect")
        .attr("x", function(d) { return users.indexOf(d.name) * gridSize; })
        .attr("y", function(d) { return days.indexOf(d.day) * gridSize; })
        .attr("rx", 4)
        .attr("ry", 4)
        .attr("class", "activity bordered")
        .attr("width", gridSize)
        .attr("height", gridSize)
        .style("fill", colors[0]);

    heatMap.transition().duration(1500)
        .style("fill", function(d) { return activityScale(d.value); });

    heatMap.append("title").text(function(d) { return d.value; });

    var legend = svg.selectAll(".legend")
        .data(activityScale.domain(), function(d) { return d; })
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
      .text(function(d) { return d; })
      .attr("x", function(d, i) { return legendElementWidth * i; })
      .attr("y", height + gridSize);
  });
});
