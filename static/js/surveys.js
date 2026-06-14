const surveyForm = document.querySelector("#surveyForm");
const surveyMessage = document.querySelector("#surveyMessage");

function formToJson(form) {
  const data = {};
  const fm = new FormData(form);
  // Handle multiple checkbox groups
  const multiple = {};
  for (const [key, value] of fm.entries()) {
    if (key.endsWith("[]") ) continue;
    if (data[key] === undefined) {
      data[key] = value;
    } else {
      // convert to array if repeated
      if (!Array.isArray(data[key])) data[key] = [data[key]];
      data[key].push(value);
    }
  }

  // collect checkbox groups specifically
  // who_talked and contraceptive_methods may have multiple values
  data["who_talked"] = Array.from(form.querySelectorAll("input[name=who_talked]:checked")).map(i => i.value);
  data["contraceptive_methods"] = Array.from(form.querySelectorAll("input[name=contraceptive_methods]:checked")).map(i => i.value);

  // boolean checkboxes
  ["receivedSexEducation","schoolEducation","needMoreInformation","pressuredToHaveSex","feelsEmbarrassed","friends_discuss","support_structure","contraceptiveUse"].forEach(name => {
    const el = form.querySelector(`[name=${name}]`);
    if (!el) return;
    data[name] = el.type === 'checkbox' ? el.checked : (el.value === 'true');
  });

  // radios for yes/no
  const hadSex = form.querySelector('input[name=had_sexual_relations]:checked');
  data['had_sexual_relations'] = hadSex ? (hadSex.value === 'true') : false;
  const hadStd = form.querySelector('input[name=had_std]:checked');
  data['had_std'] = hadStd ? (hadStd.value === 'true') : false;

  // other optional fields
  data['std_details'] = form.querySelector('[name=std_details]')?.value || '';
  data['support_structure_location'] = form.querySelector('[name=support_structure_location]')?.value || '';

  // normalize numeric
  if (data.age) data.age = parseInt(data.age, 10);

  return data;
}

surveyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = formToJson(surveyForm);
  const response = await apiFetch("/surveys", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  surveyMessage.textContent = result.message || JSON.stringify(result);
  surveyMessage.className = response.ok ? "text-success" : "text-danger";
  if (response.ok) surveyForm.reset();
});
