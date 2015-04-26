(function () {
  'use strict';

  var ip = "http://192.168.2.113:8080";

  var place = window.location.search.substring(1).split('=')[1];
  $('.analysis-name').text('Place: ' + place);

  // initialise the data
  $.get(ip + '/get_analysis', {'place': place}, function(data) {

    // populate the basic info about the place first
    $('.place-info .visit-date').text(data.visit_date);
    $('.place-info .num-counters').text(data.num_counters);
    if (data.is_pooled === 1) {
      $('.place-info .pooled-boolean').text('Pooled');
    } else {
      $('.place-info .pooled-boolean').text('Non-Pooled');
    }
    $('.place-info .num-datapoints').text(data.num_datapoints);

    // populate the summary statistics
    $.each(data.summary, function(index, item) {
      $('.stat-box.' + item[0] + ' .stat-num').text(item[1].toFixed(2));
    });

    // initialise the line charts
    var options = {
      showLine: false,
      chartPadding: {
        right: 15
      },
      plugins: [
          ctMissingData({
            showMissingDataPoints: false
          })
      ],
      axisX: {
        labelInterpolationFnc: function(value, index) {
          return index % 13 === 0 ? value : null;
        }
      }
    };

    var responsiveOptions = [
      ['screen and (min-width: 640px)', {
        axisX: {
          labelInterpolationFnc: function(value, index) {
            return index % 4 === 0 ? value : null;
          }
        }
      }]
    ];

    // plot the scatterplots
    new Chartist.Line('#interarrival', data.interarrival, options, responsiveOptions);
    new Chartist.Line('#waiting_time', data.waiting, options, responsiveOptions);

    // plot the histogram
    var histogram_options = {
      stackBars: true,
      axisY: {
        labelInterpolationFnc: function(value) {
          return (value / 1);
        }
      }
    };

    new Chartist.Bar('#processing', data.processing, histogram_options).on('draw', function(data) {
      if (data.type === 'bar') {
        data.element.attr({
          style: 'stroke-width: 30px'
        });
      }
    });

  });

})();