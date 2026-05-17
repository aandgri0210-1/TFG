document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-autosubmit]').forEach((element) => {
    element.addEventListener('change', () => {
      const form = element.closest('form');
      if (form) {
        form.submit();
      }
    });
  });

  const debounce = (callback, wait) => {
    let timeoutId;
    return (...args) => {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => callback(...args), wait);
    };
  };

  document.querySelectorAll('[data-location-autocomplete]').forEach((input) => {
    const form = input.closest('form');
    const resultsBox = form ? form.querySelector('[data-location-results]') : null;
    const cityField = form ? form.querySelector('input[name="city"]') : null;
    const placeIdField = form ? form.querySelector('input[name="location_place_id"]') : null;
    const latitudeField = form ? form.querySelector('input[name="latitude"]') : null;
    const longitudeField = form ? form.querySelector('input[name="longitude"]') : null;
    const endpoint = input.dataset.locationUrl || '/servicios/localidades/';
    // reverse endpoint for geolocation lookup
    const reverseEndpoint = endpoint.replace(/localidades\/?$/, 'localidades/reverse/');

    if (!resultsBox || !cityField || !placeIdField || !latitudeField || !longitudeField) {
      return;
    }

    const clearSelection = () => {
      cityField.value = '';
      placeIdField.value = '';
      latitudeField.value = '';
      longitudeField.value = '';
    };

    const renderResults = (items) => {
      resultsBox.innerHTML = '';
      if (!items.length) {
        resultsBox.hidden = true;
        return;
      }

      items.forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'location-result';
        button.innerHTML = `
          <strong>${item.label}</strong>
          <span>${item.municipality || ''}${item.country ? ` · ${item.country}` : ''}</span>
        `;

        button.addEventListener('click', () => {
          input.value = item.label;
          cityField.value = item.label;
          placeIdField.value = item.place_id;
          latitudeField.value = item.latitude;
          longitudeField.value = item.longitude;
          resultsBox.innerHTML = '';
          resultsBox.hidden = true;
        });

        resultsBox.appendChild(button);
      });

      resultsBox.hidden = false;
    };

    // Add support for "Ubicación actual" button if present
    const currentBtn = form ? form.querySelector('[data-use-current-location]') : null;
    if (currentBtn) {
      currentBtn.addEventListener('click', () => {
        if (!navigator.geolocation) {
          currentBtn.textContent = 'Geolocalización no soportada';
          setTimeout(() => currentBtn.textContent = 'Ubicación actual', 2000);
          return;
        }
        currentBtn.disabled = true;
        currentBtn.textContent = 'Obteniendo…';

        navigator.geolocation.getCurrentPosition(async (pos) => {
          try {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            const resp = await fetch(`${reverseEndpoint}?lat=${lat}&lon=${lon}`);
            const payload = await resp.json();
            const r = payload.result;
            if (r) {
              // show only the current location as selectable option
              const item = {
                place_id: r.place_id,
                label: `Ubicación actual — ${r.label}`,
                municipality: r.municipality || r.label,
                country: r.country || 'ES',
                latitude: r.latitude,
                longitude: r.longitude,
              };
              renderResults([item]);
            } else {
              resultsBox.innerHTML = '';
              resultsBox.hidden = true;
            }
          } catch (err) {
            resultsBox.innerHTML = '';
            resultsBox.hidden = true;
          } finally {
            currentBtn.disabled = false;
            currentBtn.textContent = 'Ubicación actual';
          }
        }, (err) => {
          currentBtn.disabled = false;
          currentBtn.textContent = 'Ubicación actual';
        }, { enableHighAccuracy: false, timeout: 8000 });
      });
    }

    const searchLocations = debounce(async () => {
      const query = input.value.trim();
      clearSelection();

      if (query.length < 2) {
        resultsBox.innerHTML = '';
        resultsBox.hidden = true;
        return;
      }

      try {
        const response = await fetch(`${endpoint}?q=${encodeURIComponent(query)}`);
        const payload = await response.json();
        renderResults(payload.results || []);
      } catch (error) {
        resultsBox.innerHTML = '';
        resultsBox.hidden = true;
      }
    }, 220);

    input.addEventListener('input', searchLocations);
    input.addEventListener('blur', () => {
      window.setTimeout(() => {
        if (!placeIdField.value) {
          resultsBox.hidden = true;
        }
      }, 150);
    });
  });

  document.querySelectorAll('[data-rating-widget]').forEach((widget) => {
    const allInputs = Array.from(widget.querySelectorAll('input[name="rating"]'));
    const starButtons = Array.from(widget.querySelectorAll('[data-star-index]'));
    const display = widget.querySelector('[data-rating-display]');
    const note = widget.querySelector('[data-rating-note]');
    const inputByValue = new Map(allInputs.map((input) => [parseFloat(input.value), input]));

    if (!allInputs.length || !starButtons.length || !display) {
      return;
    }

    const getStarValue = (starNumber, isLeftHalf) => {
      if (starNumber === 1) {
        return 1.0;
      }
      return isLeftHalf ? starNumber - 0.5 : starNumber;
    };

    const render = (value) => {
      const selectedValue = value ? parseFloat(value) : 0;

      display.textContent = `${selectedValue}/5`;
      if (note) {
        note.textContent = selectedValue 
          ? `Has elegido ${selectedValue} de 5` 
          : 'Selecciona una puntuación';
      }

      starButtons.forEach((button) => {
        const starNumber = parseInt(button.dataset.starIndex, 10);

        button.classList.remove('is-active', 'is-half');

        if (selectedValue >= starNumber) {
          button.classList.add('is-active');
        } else if (selectedValue >= starNumber - 0.5 && selectedValue < starNumber) {
          button.classList.add('is-half');
        }
      });
    };

    const setRating = (ratingValue) => {
      const targetInput = inputByValue.get(parseFloat(ratingValue));
      if (!targetInput) return;
      targetInput.checked = true;
      targetInput.dispatchEvent(new Event('change', { bubbles: true }));
      render(targetInput.value);
    };

    starButtons.forEach((button) => {
      const handlePointer = (event) => {
        const rect = button.getBoundingClientRect();
        const isLeftHalf = event.clientX - rect.left < rect.width / 2;
        const starNumber = parseInt(button.dataset.starIndex, 10);
        return getStarValue(starNumber, isLeftHalf);
      };

      button.addEventListener('mousemove', (event) => {
        render(handlePointer(event));
      });

      button.addEventListener('mouseleave', () => {
        const checkedInput = widget.querySelector('input[name="rating"]:checked');
        render(checkedInput ? checkedInput.value : 0);
      });

      button.addEventListener('click', (event) => {
        event.preventDefault();
        setRating(handlePointer(event));
      });

      button.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          const starNumber = parseInt(button.dataset.starIndex, 10);
          setRating(starNumber);
        }
      });
    });

    allInputs.forEach((input) => {
      input.addEventListener('change', () => {
        render(input.value);
      });
    });

    const checkedInput = widget.querySelector('input[name="rating"]:checked');
    if (checkedInput) {
      render(checkedInput.value);
    } else {
      render(0);
    }
  });

  // Handle vehicle fields visibility based on listing type
  const listingType = document.querySelector('[name="listing_type"]');
  const vehicleFields = Array.from(document.querySelectorAll('[data-vehicle-field]'));

  if (listingType && vehicleFields.length) {
    const toggleVehicleFields = () => {
      // Normalize comparison: check if it matches "Vender vehiculo" (case-insensitive)
      const show = listingType.value.toLowerCase() === 'vender vehiculo';
      vehicleFields.forEach((field) => {
        field.hidden = !show;
      });
    };

    listingType.addEventListener('change', toggleVehicleFields);
    toggleVehicleFields();
  }

});
