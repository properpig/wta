(function () {
  'use strict';

  var ip = "http://192.168.2.113:8080";

  // initialise the page
  if (localStorage.getItem('place') === null) {
    localStorage.setItem('place', 'matcha'); // defaults to matcha. will change later
  }

  var place = localStorage.getItem('place');
  var num_counters;
  $.get( ip + "/retrieve_queue_info", {'place': place}, function( data ) {
    place = data.place;
    num_counters = data.num_counters;
    $('.app-title .place-name').text(place);

    // iterate through the alphabets (they are our queue ids)
    for(var i=65;i<65+num_counters;i++) {
      var queue_id = String.fromCharCode(i);
      $('.counters').append(getCounterHTML(queue_id));
      $('.queues').append(getQueueHTML(queue_id));
      $('.add-buttons').append(getButtonHTML(queue_id));
    }

    // set the width of each column so they all fit
    var col_percent = 100/num_counters;
    $('.general-container').css({'width': col_percent+'%'});
  })
  .done(function() {
    // can only do this after we get the numbers
    populateQueues();
  });

  function populateQueues() {
    // initialise the state of the queues
    $.get( ip + "/retrieve_queues", {'place': place}, function( data ) {
      // loop through each person and put him in the right queue
      $.each(data, function(index, item) {
        $('.queue-container.' + item.queue).append(getPersonHTML(item.person_id));
        // check if this person is being served
        if (item.is_being_served) {
          // visual indication to the counter and the person in line
          $('.pid-' + item.person_id).addClass('processing');
          $('.counter-container.' + item.queue).addClass('processing');
        }
      });
    })
    .done(function() {
      attachEventHandlers();
    });
  }

  // event handlers
  function attachEventHandlers() {
    // to indicate a person being served
    $('.counter-container').click(function() {
      // get the queue first (i.e. A, B, C..)
      var classList = $(this).attr('class').split(/\s+/);
      var queue_id = getQueueId(classList);
      console.log(queue_id);

      // now we find the corresponding queue to get the id of the first person
      // first check if there are any people queuing
      if ($('.queue-container.' + queue_id + ' .person').length === 0) {
        console.log('error, there is no one in the queue!');
        return;
      }

      var person = $('.queue-container.' + queue_id + ' .person').first();
      var person_id = person.text();

      var this_counter = $(this);

      // this counter is about to process the next person
      if (!$(this).hasClass('processing')) {
        // inform the backend
        $.get( ip + "/process_person", {'person_id': person_id}, function( data ) {
          console.log(data);
        })
        .done(function() {
          person.addClass('processing');
          this_counter.addClass('processing'); // visual update to the counter
        });

      } else {
        // this counter is done processing the current person
        $.get( ip + "/process_complete", {'person_id': person_id}, function( data ) {
          console.log(data);
        })
        .done(function() {
          person.remove();
          this_counter.removeClass('processing'); // visual update to the counter
        });
      }
    });

    // to indicate a person joining the queue
    $('.button-container').click(function() {
      // visual indicator that this is clicked
      var clicked_button = $(this).children().first();
      clicked_button.addClass('clicked');
      setTimeout(function(){
        clicked_button.removeClass('clicked');
      }, 300);

      // get the queue first (i.e. A, B, C..)
      var classList = $(this).attr('class').split(/\s+/);
      var queue_id = getQueueId(classList);

      var person_id = "";
      // backend call to create the person; returns the id
      var params = {'queue_id': queue_id, 'place': place};
      $.get( ip + "/add_person", params, function( data ) {
        person_id = data.pid;
      })
      .done(function() {
        $('.queue-container.' + queue_id).append(getPersonHTML(person_id));
      });

    });

    // to hide a counter

    // to allow deletion of a person in the queue
    $('.dialog .confirm').click(function() {
      var person_id = $('.dialog').data('pid');
      // send call to backend
      var params = {'person_id': person_id};
      $.get( ip + "/delete_person", params, function( data ) {
        console.log(data);
      })
      .done(function() {
        $('.pid-' + person_id).remove();
        $('.dialog').removeClass('open');
      });
    });

    $('.dialog .cancel').click(function() {
      var person_id = $('.dialog').data('pid');
      $('.pid-' + person_id).removeClass('selected');
      $('.dialog').removeClass('open');
    });
  }

  function getQueueId(classList) {
    var queue_id = "";
    $.each(classList, function(index, item) {
      if (item.length == 1) {
        queue_id = item;
      }
    });
    return queue_id;
  }

  function getPersonHTML(person_id) {
    return '<div class="person pid-' + person_id + '" onclick="removePerson(' + person_id + ')">' + person_id + '</div>';
  }

  function getCounterHTML(queue_id) {
    /*jshint multistr: true */
    return '<div class="general-container counter-container ' + queue_id + '">\
              <div class="counter">' + queue_id + '</div>\
            </div>';
  }

  function getQueueHTML(queue_id) {
    return '<div class="general-container queue-container ' + queue_id + '"></div>';
  }

  function getButtonHTML(queue_id) {
    /*jshint multistr: true */
    return '<div class="general-container button-container ' + queue_id + '"> \
              <div class="add-button"></div> \
            </div>';
  }



})();

/*exported removePerson */
function removePerson(id) {
  // check if there is already a selected person
  if ($('.person.selected').length !== 0) {
    return;
  }
  $('.pid-' + id).addClass('selected');
  $('.dialog').addClass('open');
  $('.dialog').data('pid', id);
  $('.dialog').data('type', 'remove_person'); // dialog can either be to remove people or to hide a counter
}