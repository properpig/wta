/*!
 *
 *  Web Starter Kit
 *  Copyright 2014 Google Inc. All rights reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *    https://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License
 *
 */
 var ip = "http://192.168.2.113:8080";

(function () {
  'use strict';

  var querySelector = document.querySelector.bind(document);

  var navdrawerContainer = querySelector('.navdrawer-container');
  var body = document.body;
  var appbarElement = querySelector('.app-bar');
  var menuBtn = querySelector('.menu');
  var refreshBtn = querySelector('.refresh');
  var main = querySelector('main');

  function closeMenu() {
    body.classList.remove('open');
    appbarElement.classList.remove('open');
    navdrawerContainer.classList.remove('open');
  }

  function toggleMenu() {
    body.classList.toggle('open');
    appbarElement.classList.toggle('open');
    navdrawerContainer.classList.toggle('open');
    navdrawerContainer.classList.add('opened');
  }

  function refreshPage() {
    location.reload();
  }

  main.addEventListener('click', closeMenu);
  menuBtn.addEventListener('click', toggleMenu);
  refreshBtn.addEventListener('click', refreshPage);

  // populate the list of available places
  $.get(ip + "/retrieve_places", function( data ) {
    $.each(data, function(index, item) {
      // add it to the list of places on the navigation menu
      $('.place-list').append('<div class="item" onclick="changePlace(\'' + item + '\');">' + item + '</div>');
      // add to the list of analysis options as well
      $('.analysis-list').append('<div class="item" onclick="launchAnalysis(\'' + item + '\');">' + item + '</div>');
    });
  });

  $('.navdrawer-container li').click(function() {
    $(this).find('.sub-menu').addClass('open');
  });

  $('.pool-option').click(function() {
    // remove selected class from both buttons first
    $('.pool-option').removeClass('selected');
    // add selected class to the clicked button
    $(this).addClass('selected');
  });

  $('.submit-button').click(function(){
    var place = $('#place_name').val();
    var num_counters = $('#num_counters').val();
    var is_pooled = false;
    if ($('.pool-option.pooled').hasClass('selected')) {
      is_pooled = true;
    }

    if (place.length === 0 || parseInt(num_counters) < 1) {
      return;
    }

    $.get(ip + "/add_place", {'place': place, 'num_counters': num_counters, 'is_pooled': is_pooled}, function( data ) {
      console.log(data);
      localStorage.setItem("place", place);
      location.reload();
    });

  });

})();

/*exported changePlace */
function changePlace(name) {
  localStorage.setItem('place', name);
  location.reload();
}

/*exported launchAnalysis */
function launchAnalysis(name) {
  location.href = 'analysis.html?place=' + name;
}
