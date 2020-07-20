import $ from "jquery";

const ratingForm = () => {
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
  });
};

$(function () {
  if ($(".js-rating")) {
    ratingForm();
  }
});
