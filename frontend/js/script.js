import $ from "jquery";

const ratingForm = () => {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie("csrftoken");

  $('input[type="number"]').each(function () {
    let $this = $(this);
    let $html = $(`<div class="rating__input" />`);
    let initial_value = $(this).val();

    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "N/A"].forEach((i) => {
      let button = $(
        `<button class="rating__button ${
          initial_value === i.toString() ? "active" : ""
        }">${i}</button>`
      );
      button.on("click", function () {
        let val = i;
        if (i === "N/A") {
          val = 0;
        }

        $this.val(val);
        $(this).siblings().removeClass("active");
        $(this).addClass("active");

        return false;
      });
      $html.append(button);
    });

    $this.addClass("absolute -z-10 -top-2").parent().addClass("relative");
    $this.parent("p").append($html);
  });

  $("#id_is_conflict, #id_is_draft").on("click", function () {
    let is_checked_conflict = $("#id_is_conflict").is(":checked");
    let is_checked_draft = $("#id_is_draft").is(":checked");

    const is_checked = is_checked_conflict || is_checked_draft;

    $('input[type="number"]').each(function () {
      if (is_checked) {
        $(this).removeAttr("required");
      } else {
        $(this).prop("required", true);
      }
    });

    console.log("boop");
    if ($("#id_individual")) {
      console.log("beep");
      if (is_checked) {
        $("#id_comment").removeAttr("required");
      } else {
        $("#id_comment").prop("required", true);
      }
    }
  });

  $(".js-reviewers li").each(function () {
    $(this).on("click", function () {
      let user = $(this).data("user");
      let entry = $(this).data("entry");
      let ignore = $(this).data("ignore");

      if (!ignore) {
        function csrfSafeMethod(method) {
          // these HTTP methods do not require CSRF protection
          return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
        }

        $.ajaxSetup({
          beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
          },
        });

        $.post(`/submissions/${entry}/${user}/`).then(function () {
          window.location.reload();
        });
      }

      return false;
    });
  });
};

$(function () {
  if ($(".js-rating")) {
    ratingForm();
  }
});
