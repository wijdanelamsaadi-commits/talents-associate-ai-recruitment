(function () {
  function setMessage(form, text, type) {
    var messageBox = form.querySelector("[data-talents-candidate-message]");
    if (!messageBox) {
      return;
    }
    messageBox.textContent = text;
    messageBox.classList.remove("is-success", "is-error");
    messageBox.classList.add(type === "success" ? "is-success" : "is-error");
  }

  function bindForm(form) {
    if (!form || form.dataset.talentsBound === "true") {
      return;
    }
    form.dataset.talentsBound = "true";

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var submitButton = form.querySelector('button[type="submit"]');
      if (submitButton && submitButton.disabled) {
        return;
      }

      var cvInput = form.querySelector('input[name="cv"]');
      if (!cvInput || !cvInput.files || cvInput.files.length === 0) {
        setMessage(form, TalentsCandidateBridge.missingCv, "error");
        return;
      }

      var formData = new FormData(form);
      formData.set("action", TalentsCandidateBridge.action);
      formData.set("talents_candidate_nonce", TalentsCandidateBridge.nonce);

      var originalText = submitButton ? submitButton.textContent : "";
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = TalentsCandidateBridge.loadingText;
      }

      fetch(TalentsCandidateBridge.ajaxUrl, {
        method: "POST",
        credentials: "same-origin",
        body: formData
      })
        .then(function (response) {
          return response.json().then(function (payload) {
            return { ok: response.ok, payload: payload };
          });
        })
        .then(function (result) {
          var payload = result.payload || {};
          var message = payload.data && payload.data.message ? payload.data.message : TalentsCandidateBridge.genericError;
          if (payload.success) {
            setMessage(form, message || TalentsCandidateBridge.successText, "success");
            form.reset();
            return;
          }
          setMessage(form, message, "error");
        })
        .catch(function () {
          setMessage(form, TalentsCandidateBridge.genericError, "error");
        })
        .finally(function () {
          if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
          }
        });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-talents-candidate-form]").forEach(bindForm);
  });
})();
