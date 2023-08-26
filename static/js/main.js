// /js/main.js
// add hovered class to selected list item
let list = document.querySelectorAll(".sidebar li");

function activeLink() {
  list.forEach((item) => {
    item.classList.remove("hovered");
  });
  this.classList.add("hovered");
}

list.forEach((item) => item.addEventListener("mouseover", activeLink));

// Menu Toggle
let toggle = document.querySelector(".toggle");
let sidebar = document.querySelector(".sidebar");
let main = document.querySelector(".main");

toggle.onclick = function () {
  sidebar.classList.toggle("active");
  main.classList.toggle("active");
};

// main.js

// main.js

// main.js

// Function to show the popup textarea
function showPopup(input) {
  var popup = input.nextElementSibling;
  popup.style.display = "block";
}

// Function to hide the popup textarea
function hidePopup(button) {
  var popup = button.parentNode;
  popup.style.display = "none";
}

// Add event listeners to all input fields with the name "commentbox"
document.addEventListener("DOMContentLoaded", function() {
  var commentboxes = document.querySelectorAll("input[name='commentbox']");

  commentboxes.forEach(function(commentbox) {
    commentbox.addEventListener("click", function() {
      showPopup(this);
    });

    commentbox.addEventListener("blur", function() {
      hidePopup(this.nextElementSibling.querySelector("button"));
    });
  });

  var closeButtons = document.querySelectorAll(".popup button");

  closeButtons.forEach(function(button) {
    button.addEventListener("click", function() {
      hidePopup(this);
    });
  });
});
