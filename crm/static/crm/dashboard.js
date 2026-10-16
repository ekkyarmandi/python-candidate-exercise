// Renders the CRM screen from the JSON payloads embedded by the template.
(function () {
  'use strict';

  function loadJson(id) {
    return JSON.parse(document.getElementById(id).textContent);
  }

  function readServerData() {
    return document.getElementById('server-data').dataset;
  }

  function readCsrfToken() {
    var match = document.cookie.match(/csrftoken=([^;]+)/);
    return (match || [, ''])[1];
  }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function statusOptions(selected) {
    var options = '';
    for (var i = 0; i < window.CRM_STATUS_CHOICES.length; i++) {
      var choice = window.CRM_STATUS_CHOICES[i];
      options += '<option value="' + choice[0] + '" ' + (selected === choice[0] ? 'selected' : '') + '>' + choice[1] + '</option>';
    }
    return options;
  }

  function renderStats(data) {
    return '<div class="stats">'
      + '<div class="stat"><b>' + esc(data.total) + '</b><div class="muted">All contacts</div></div>'
      + '<div class="stat"><b>$' + Number(data.pipeline).toLocaleString() + '</b><div class="muted">Pipeline value</div></div>'
      + '</div>';
  }

  function renderToolbar(data) {
    return '<div class="toolbar"><form method="get">'
      + '<input name="q" value="' + esc(data.q) + '" placeholder="Search name, company, email">'
      + '<select name="status"><option value="">All statuses</option>' + statusOptions(data.status) + '</select>'
      + '<button class="btn">Search</button><a href="/export/" style="padding:9px">Export CSV</a>'
      + '</form></div>';
  }

  function renderRow(contact) {
    return '<a class="row ' + (contact.selected ? 'selected' : '') + '" href="' + esc(contact.url) + '">'
      + '<span><b>' + esc(contact.name) + '</b><div class="muted">' + esc(contact.email) + '</div></span>'
      + '<span>' + esc(contact.company) + '</span>'
      + '<span><span class="pill">' + esc(contact.status_label) + '</span></span>'
      + '<span>$' + Number(contact.value).toLocaleString() + '</span>'
      + '</a>';
  }

  function renderNewContactBox(csrf) {
    return '<div class="newbox"><b>Add contact</b><form method="post">'
      + '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'
      + '<input type="hidden" name="action" value="add_contact">'
      + '<input name="name" placeholder="Name"><input name="email" placeholder="Email">'
      + '<input name="company" placeholder="Company"><input name="owner" placeholder="Owner">'
      + '<input name="phone" placeholder="Phone"><input name="value" placeholder="Value">'
      + '<select name="new_status">' + statusOptions('lead') + '</select>'
      + '<button class="btn">Add</button></form></div>';
  }

  function renderContactsPanel(contacts, csrf) {
    var html = '<div class="panel"><h2>Contacts</h2><div class="list">';
    for (var i = 0; i < contacts.length; i++) {
      html += renderRow(contacts[i]);
    }
    if (!contacts.length) {
      html += '<p style="padding:20px">No contacts found.</p>';
    }
    html += '</div>';
    html += renderNewContactBox(csrf);
    html += '</div>';
    return html;
  }

  function renderActivities(activities) {
    var html = '';
    for (var i = 0; i < activities.length; i++) {
      var activity = activities[i];
      html += '<p><span class="pill">' + esc(activity.kind) + '</span> ' + esc(activity.body)
        + '<br><span class="muted">' + esc(activity.created_at) + '</span></p>';
    }
    return html;
  }

  function renderDetailActions(detail, csrf) {
    return '<div class="actions">'
      + '<form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'
      + '<input type="hidden" name="action" value="change_status">'
      + '<input type="hidden" name="contact_id" value="' + detail.id + '">'
      + '<select name="new_status">' + statusOptions(detail.status) + '</select>'
      + '<button class="btn">Update status</button></form>'
      + '<form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'
      + '<input type="hidden" name="action" value="add_note">'
      + '<input type="hidden" name="contact_id" value="' + detail.id + '">'
      + '<textarea name="note" placeholder="Add a note"></textarea>'
      + '<button class="btn">Save note</button></form>'
      + '<form method="post" onsubmit="return confirm(&quot;Delete this contact?&quot;)">'
      + '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'
      + '<input type="hidden" name="action" value="delete_contact">'
      + '<input type="hidden" name="contact_id" value="' + detail.id + '">'
      + '<button class="btn danger">Delete contact</button></form>'
      + '<h4>Activity</h4>'
      + renderActivities(detail.activities)
      + '</div>';
  }

  function renderDetailBody(detail, csrf) {
    return '<h3>' + esc(detail.name) + '</h3>'
      + '<dl>'
      + '<dt>Company</dt><dd>' + esc(detail.company) + '</dd>'
      + '<dt>Email</dt><dd>' + esc(detail.email) + '</dd>'
      + '<dt>Phone</dt><dd>' + esc(detail.phone) + '</dd>'
      + '<dt>Owner</dt><dd>' + esc(detail.owner) + '</dd>'
      + '<dt>Value</dt><dd>$' + Number(detail.value).toLocaleString() + '</dd>'
      + '</dl>'
      + renderDetailActions(detail, csrf);
  }

  function renderDetailPanel(detail, csrf) {
    var html = '<div class="panel"><h2>Contact details</h2><div class="detail">';
    html += detail ? renderDetailBody(detail, csrf) : '<p>Select a contact.</p>';
    html += '</div></div>';
    return html;
  }

  function render() {
    var contacts = loadJson('contacts-data');
    var detail = loadJson('detail-data');
    var data = readServerData();
    var csrf = readCsrfToken();

    var html = '<div class="top">Jellybean CRM</div><div class="wrap">';
    if (data.error) {
      html += '<div class="error">' + esc(data.error) + '</div>';
    }
    html += renderStats(data);
    html += renderToolbar(data);
    html += '<div class="grid">';
    html += renderContactsPanel(contacts, csrf);
    html += renderDetailPanel(detail, csrf);
    html += '</div></div>';

    document.getElementById('crm-app').innerHTML = html;
  }

  render();
})();
