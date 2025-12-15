document.addEventListener('DOMContentLoaded', function () {

    function renderRecipeStars(container, rating) {
      let html = '';
      for (let i = 1; i <= 5; i++) {
        if (rating >= i) {
          html += '<i class="bi bi-star-fill"></i> ';
        } else if (rating >= i - 0.5) {
          html += '<i class="bi bi-star-half"></i> ';
        } else {
          html += '<i class="bi bi-star"></i> ';
        }
      }
      container.innerHTML = html;
    }

    const badges = document.querySelectorAll('.recipe-rating-badge');
    badges.forEach(badge => {
      const avg = parseFloat(badge.dataset.averageRating) || 0;
      const starsContainer = badge.querySelector('.recipe-stars');
      if (starsContainer) {
        renderRecipeStars(starsContainer, avg);
      }
    });
  });

  window.addEventListener('pageshow', function (event) {
    if (event.persisted) {
      window.location.reload();
    }
  });