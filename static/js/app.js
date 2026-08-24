document.addEventListener('DOMContentLoaded', () => {
  const goalSelect = document.getElementById('goal-select');
  const worldSelect = document.getElementById('world-select');
  const predicateSelect = document.getElementById('predicate-select');
  const argumentContainer = document.getElementById('argument-container');
  const actionLog = document.getElementById('action-log');
  const speedSlider = document.getElementById('speed-slider');
  const speedValue = document.getElementById('speed-value');
  const statusDot = document.getElementById('status-dot');
  const headerStatus = document.getElementById('header-status');
  const footerStatusDot = document.getElementById('footer-status-dot');
  const footerStatusText = document.getElementById('footer-status-text');
  const headerGoal = document.getElementById('header-goal');
  const headerWorld = document.getElementById('header-world');
  const toast = document.getElementById('toast');

  let toastTimer = null;
  let worldObjects = [];
  let recording = false;
  let recordedActions = [];
  const recordButton = document.getElementById('btn-record');
  const saveGoalButton = document.getElementById('btn-save-goal');
  const recordingStatus = document.getElementById('recording-status');
  const runAllButton = document.getElementById('btn-run-all');
  const newGoalButton = document.getElementById('btn-new-goal');
  const goalModal = document.getElementById('goal-modal');
  const goalNameInput = document.getElementById('goal-name-input');
  const recordedActionsPreview = document.getElementById('recorded-actions-preview');

  function updateNewGoalButton() {
    if (newGoalButton) newGoalButton.disabled = recording || recordedActions.length === 0;
  }

  function openGoalModal() {
    if (!goalModal) return;
    recordedActionsPreview.value = recordedActions.map((action, index) =>
      `${index + 1}. ${action.name}(${(action.args || []).join(', ')})`
    ).join('\n');
    goalNameInput.value = '';
    goalModal.hidden = false;
    goalNameInput.focus();
  }

  function closeGoalModal() {
    if (goalModal) goalModal.hidden = true;
  }

  function setGlobalStatus(text, mode = 'online') {
    const targetDot = statusDot || footerStatusDot;
    const targetText = headerStatus || footerStatusText;
    const dotClass = mode === 'online' ? 'online' : mode === 'busy' ? 'busy' : 'offline';

    if (targetDot) {
      targetDot.className = `status-dot ${dotClass}`;
    }
    if (targetText) {
      targetText.textContent = text;
    }
    if (footerStatusText) {
      footerStatusText.textContent = text;
    }
    if (footerStatusDot) {
      footerStatusDot.className = `status-dot ${dotClass}`;
    }
  }

  function addLog(message, kind = 'info') {
    if (!actionLog) return;

    const stamp = document.createElement('div');
    stamp.className = `log-entry ${kind}`;
    stamp.innerHTML = `<span class="timestamp">${new Date().toLocaleTimeString()}</span>${message}`;
    actionLog.appendChild(stamp);
    actionLog.scrollTop = actionLog.scrollHeight;
  }

  function showToast(message, kind = 'info') {
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast show ${kind}`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.className = 'toast';
    }, 3200);
  }

  async function request(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed (${response.status})`);
    }
    return response;
  }

  function refreshSelectedMeta() {
    if (headerGoal) {
      headerGoal.textContent = goalSelect && goalSelect.value ? goalSelect.value : 'Select goal';
    }
    if (headerWorld) {
      headerWorld.textContent = worldSelect && worldSelect.value ? worldSelect.value : 'Select world';
    }
  }

  async function refreshWorldObjects() {
    const world = worldSelect ? worldSelect.value : '';
    if (!world) {
      worldObjects = [];
      return;
    }

    try {
      const response = await request(`/get_objects_for_world?world=${encodeURIComponent(world)}`);
      const data = await response.json();
      worldObjects = Array.isArray(data.objects) ? data.objects : [];
    } catch (error) {
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  }

  async function populateGoalsForWorld() {
    const world = worldSelect ? worldSelect.value : '';
    if (!goalSelect || !worldSelect) return;

    try {
      const response = await request(`/get_goals?world=${encodeURIComponent(world)}`);
      const data = await response.json();
      const goals = Array.isArray(data.goals) ? data.goals : [];
      const current = goalSelect.value;

      goalSelect.innerHTML = '<option value="">Select a goal...</option>';
      if (!goals.length) goalSelect.innerHTML = '<option value="">No saved goals. Create one!</option>';
      goals.forEach((goal) => {
        const option = document.createElement('option');
        option.value = goal;
        option.textContent = goal;
        goalSelect.appendChild(option);
      });

      if (goals.includes(current)) {
        goalSelect.value = current;
      }

      refreshSelectedMeta();
      if (runAllButton) runAllButton.disabled = !goalSelect.value || !goalSelect.value.includes('/user_goals/');
    } catch (error) {
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  }

  function renderActionArguments(predicate) {
    if (!argumentContainer || !predicate) {
      argumentContainer.innerHTML = '';
      return;
    }

    fetch(`/arguments?predicate=${encodeURIComponent(predicate)}`)
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load action arguments.');
        return response.text();
      })
      .then((html) => {
        argumentContainer.innerHTML = html;
      })
      .catch((error) => {
        addLog(error.message, 'error');
        showToast(error.message, 'error');
      });
  }

  function collectArguments() {
    const fields = argumentContainer.querySelectorAll('[id^="arg"]');
    const data = new URLSearchParams();

    fields.forEach((field) => {
      if (field.id) {
        data.append(field.id, field.value);
      }
    });

    return data;
  }

  goalSelect.addEventListener('change', () => {
    refreshSelectedMeta();
  });

  worldSelect.addEventListener('change', async () => {
    refreshSelectedMeta();
    await refreshWorldObjects();
    await populateGoalsForWorld();

    const world = worldSelect.value;
    if (world) {
      addLog(`World updated: ${world}.`, 'success');
    }
  });

  predicateSelect.addEventListener('change', (event) => {
    const value = event.target.value;
    renderActionArguments(value);
  });

  speedSlider.addEventListener('input', async (event) => {
    const value = Number(event.target.value).toFixed(1);
    speedValue.textContent = `${value}x`;
    try {
      await request(`/set_speed?speed=${value}`);
      addLog(`Simulation speed updated to ${value}x.`, 'success');
    } catch (error) {
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  });

  document.getElementById('btn-start').addEventListener('click', async () => {
    const goal = goalSelect.value;
    const world = worldSelect.value;

    if (!goal || !world) {
      showToast('Select a goal and world first.', 'error');
      return;
    }

    setGlobalStatus('Starting…', 'busy');
    addLog(`Starting simulation for ${goal} in ${world}.`, 'info');

    try {
      await request('/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, world })
      });
      setGlobalStatus('Online', 'online');
      addLog('Simulation started successfully.', 'success');
      showToast('Simulation started.', 'success');
    } catch (error) {
      setGlobalStatus('Offline', 'offline');
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  });

  document.getElementById('btn-next').addEventListener('click', async () => {
    try {
      const response = await request('/next', { method: 'POST' });
      const payload = await response.json();
      addLog(payload.action ? `Playback action ${payload.index}/${payload.total} executed.` : 'Next step executed.', 'success');
      showToast('Advance executed.', 'success');
    } catch (error) {
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  });

  if (runAllButton) {
    runAllButton.addEventListener('click', async () => {
      try {
        const response = await request('/run_all', { method: 'POST' });
        const payload = await response.json();
        addLog(`Playback completed: ${payload.completed}/${payload.total} actions.`, 'success');
        showToast('Saved goal completed.', 'success');
      } catch (error) {
        addLog(error.message, 'error');
        showToast(error.message, 'error');
      }
    });
  }

  document.getElementById('btn-undo').addEventListener('click', async () => {
    try {
      await request('/undo_move');
      addLog('Undo invoked.', 'warning');
      showToast('Undo requested.', 'warning');
    } catch (error) {
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  });

  document.getElementById('btn-reset').addEventListener('click', async () => {
    try {
      await request('/reset', { method: 'POST' });
      addLog('Reset requested.', 'warning');
      showToast('Simulation reset.', 'warning');
    } catch (error) {
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  });

  document.getElementById('btn-execute').addEventListener('click', async () => {
    const predicate = predicateSelect.value;
    if (!predicate) {
      showToast('Choose an action before executing.', 'error');
      return;
    }

    const params = new URLSearchParams({ predicate });
    const fields = collectArguments();
    for (const [key, value] of fields.entries()) {
      params.append(key, value);
    }

    try {
      const response = await request('/execute_move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
        body: params.toString()
      });
      const payload = await response.json();
      if (recording && payload.action) {
        await request('/api/recording/append', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload.action)
        });
        recordedActions.push(payload.action);
      }
      addLog(payload.label ? `Action executed: ${payload.label}` : 'Action executed successfully.', 'success');
      showToast('Action sent to simulator.', 'success');
    } catch (error) {
      addLog(error.message, 'error');
      showToast(error.message, 'error');
    }
  });

  if (recordButton) {
    recordButton.addEventListener('click', async () => {
      try {
        if (!recording) {
          await request('/api/recording/start', { method: 'POST' });
          recording = true;
          recordedActions = [];
          updateNewGoalButton();
          recordButton.classList.add('recording');
          recordButton.setAttribute('aria-label', 'Stop recording');
          recordButton.title = 'Stop recording';
          if (recordingStatus) recordingStatus.hidden = false;
          showToast('Recording started.', 'success');
        } else {
          const response = await request('/api/recording/stop', { method: 'POST' });
          const data = await response.json();
          recording = false;
          recordedActions = data.actions || recordedActions;
          recordButton.classList.remove('recording');
          recordButton.setAttribute('aria-label', 'Start recording');
          recordButton.title = 'Start recording';
          if (recordingStatus) recordingStatus.hidden = true;
          updateNewGoalButton();
          showToast(`${recordedActions.length} action(s) recorded.`, 'success');
        }
      } catch (error) {
        addLog(error.message, 'error');
        showToast(error.message, 'error');
      }
    });
  }

  if (newGoalButton) newGoalButton.addEventListener('click', openGoalModal);
  document.querySelectorAll('[data-close-goal-modal]').forEach((element) => {
    element.addEventListener('click', closeGoalModal);
  });

  if (saveGoalButton) {
    saveGoalButton.addEventListener('click', async () => {
      const name = goalNameInput.value;
      if (!name || !name.trim() || !recordedActions.length) return;
      try {
        const response = await request('/api/goal/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name.trim(), world: worldSelect.value, actions: recordedActions })
        });
        const data = await response.json();
        recordedActions = [];
        closeGoalModal();
        updateNewGoalButton();
        await populateGoalsForWorld();
        if (goalSelect) goalSelect.value = data.path;
        refreshSelectedMeta();
        if (runAllButton) runAllButton.disabled = false;
        addLog(`Saved goal: ${data.goal.name}.`, 'success');
        showToast('Goal saved.', 'success');
      } catch (error) {
        addLog(error.message, 'error');
        showToast(error.message, 'error');
      }
    });
  }

  document.querySelectorAll('[data-camera]').forEach((button) => {
    button.addEventListener('click', async () => {
      const direction = button.dataset.camera;
      const urlMap = {
        left: '/rotateCameraLeft',
        right: '/rotateCameraRight',
        in: '/zoomIn',
        out: '/zoomOut'
      };

      try {
        await request(urlMap[direction], { method: 'POST' });
        addLog(`Camera ${direction} command sent.`, 'info');
      } catch (error) {
        addLog(error.message, 'error');
        showToast(error.message, 'error');
      }
    });
  });

  if (speedSlider) {
    speedSlider.value = '0.5';
    speedValue.textContent = '0.5x';
  }

  if (worldSelect && worldSelect.value) {
    refreshWorldObjects().then(() => populateGoalsForWorld());
  }

  if (goalSelect && goalSelect.value) {
    refreshSelectedMeta();
  }

  updateNewGoalButton();

  setGlobalStatus('Online', 'online');
  addLog('ToolNet control surface ready.', 'success');
  addLog('Made by iHEB BEKIR.', 'info');
});

