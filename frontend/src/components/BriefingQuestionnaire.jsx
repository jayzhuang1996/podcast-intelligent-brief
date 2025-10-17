import { useState, useEffect } from 'react';
import './BriefingQuestionnaire.css';

export default function BriefingQuestionnaire({ onGenerate, onCancel }) {
  // State for each question - always start blank
  const [motivation, setMotivation] = useState('');
  const [depthLevel, setDepthLevel] = useState('');
  const [reasoningMode, setReasoningMode] = useState('');
  const [narrativeTone, setNarrativeTone] = useState('');
  const [curiosityFocus, setCuriosityFocus] = useState('');

  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};

    if (!motivation) newErrors.motivation = 'Please select what draws you to this episode';
    if (!depthLevel) newErrors.depthLevel = 'Please select how deep to go';
    if (!reasoningMode) newErrors.reasoningMode = 'Please select a lens';
    if (!narrativeTone) newErrors.narrativeTone = 'Please select a voice';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleGenerate = () => {
    if (!validate()) return;

    const context = {
      motivation,
      depth_level: depthLevel,
      reasoning_mode: reasoningMode,
      narrative_tone: narrativeTone,
      curiosity_focus: curiosityFocus || null
    };

    onGenerate(context);
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="questionnaire-modal" onClick={(e) => e.stopPropagation()}>
        <h2>🎯 Customize Your Intelligent Briefing</h2>
        <p className="subtitle">Help us tailor the briefing to your needs</p>

        {/* Question 1 */}
        <div className="question">
          <label>1. What draws you to this episode right now?</label>
          <div className="options">
            <label className={motivation === 'topic_interesting' ? 'selected' : ''}>
              <input
                type="radio"
                value="topic_interesting"
                checked={motivation === 'topic_interesting'}
                onChange={(e) => setMotivation(e.target.value)}
              />
              <span>The topic sounds interesting</span>
            </label>
            <label className={motivation === 'speaker_perspective' ? 'selected' : ''}>
              <input
                type="radio"
                value="speaker_perspective"
                checked={motivation === 'speaker_perspective'}
                onChange={(e) => setMotivation(e.target.value)}
              />
              <span>I like the speaker's perspective</span>
            </label>
            <label className={motivation === 'personal_connection' ? 'selected' : ''}>
              <input
                type="radio"
                value="personal_connection"
                checked={motivation === 'personal_connection'}
                onChange={(e) => setMotivation(e.target.value)}
              />
              <span>It connects to something I've been thinking about</span>
            </label>
            <label className={motivation === 'cultural_relevance' ? 'selected' : ''}>
              <input
                type="radio"
                value="cultural_relevance"
                checked={motivation === 'cultural_relevance'}
                onChange={(e) => setMotivation(e.target.value)}
              />
              <span>I just want to see what everyone's talking about</span>
            </label>
          </div>
          {errors.motivation && <span className="error">{errors.motivation}</span>}
        </div>

        {/* Question 2 */}
        <div className="question">
          <label>2. How deep should we go?</label>
          <div className="options">
            <label className={depthLevel === 'essence' ? 'selected' : ''}>
              <input
                type="radio"
                value="essence"
                checked={depthLevel === 'essence'}
                onChange={(e) => setDepthLevel(e.target.value)}
              />
              <span>Just the essence — quick but sharp</span>
            </label>
            <label className={depthLevel === 'balanced' ? 'selected' : ''}>
              <input
                type="radio"
                value="balanced"
                checked={depthLevel === 'balanced'}
                onChange={(e) => setDepthLevel(e.target.value)}
              />
              <span>A balanced mix of key points and insights</span>
            </label>
            <label className={depthLevel === 'deep' ? 'selected' : ''}>
              <input
                type="radio"
                value="deep"
                checked={depthLevel === 'deep'}
                onChange={(e) => setDepthLevel(e.target.value)}
              />
              <span>Dig deep — explore the reasoning and nuance</span>
            </label>
          </div>
          {errors.depthLevel && <span className="error">{errors.depthLevel}</span>}
        </div>

        {/* Question 3 */}
        <div className="question">
          <label>3. What kind of lens should we bring to it?</label>
          <div className="options">
            <label className={reasoningMode === 'connect' ? 'selected' : ''}>
              <input
                type="radio"
                value="connect"
                checked={reasoningMode === 'connect'}
                onChange={(e) => setReasoningMode(e.target.value)}
              />
              <span>Connect ideas — show how concepts relate</span>
            </label>
            <label className={reasoningMode === 'challenge' ? 'selected' : ''}>
              <input
                type="radio"
                value="challenge"
                checked={reasoningMode === 'challenge'}
                onChange={(e) => setReasoningMode(e.target.value)}
              />
              <span>Challenge it — point out gaps or biases</span>
            </label>
            <label className={reasoningMode === 'apply' ? 'selected' : ''}>
              <input
                type="radio"
                value="apply"
                checked={reasoningMode === 'apply'}
                onChange={(e) => setReasoningMode(e.target.value)}
              />
              <span>Apply it — show how this could play out in real life</span>
            </label>
            <label className={reasoningMode === 'reflect' ? 'selected' : ''}>
              <input
                type="radio"
                value="reflect"
                checked={reasoningMode === 'reflect'}
                onChange={(e) => setReasoningMode(e.target.value)}
              />
              <span>Reflect on it — what it says about broader trends or people</span>
            </label>
          </div>
          {errors.reasoningMode && <span className="error">{errors.reasoningMode}</span>}
        </div>

        {/* Question 4 */}
        <div className="question">
          <label>4. Which voice feels right for your recap?</label>
          <div className="options">
            <label className={narrativeTone === 'analytical' ? 'selected' : ''}>
              <input
                type="radio"
                value="analytical"
                checked={narrativeTone === 'analytical'}
                onChange={(e) => setNarrativeTone(e.target.value)}
              />
              <span>Direct and analytical</span>
            </label>
            <label className={narrativeTone === 'conversational' ? 'selected' : ''}>
              <input
                type="radio"
                value="conversational"
                checked={narrativeTone === 'conversational'}
                onChange={(e) => setNarrativeTone(e.target.value)}
              />
              <span>Conversational and curious</span>
            </label>
            <label className={narrativeTone === 'thoughtful' ? 'selected' : ''}>
              <input
                type="radio"
                value="thoughtful"
                checked={narrativeTone === 'thoughtful'}
                onChange={(e) => setNarrativeTone(e.target.value)}
              />
              <span>Thoughtful and reflective</span>
            </label>
            <label className={narrativeTone === 'provocative' ? 'selected' : ''}>
              <input
                type="radio"
                value="provocative"
                checked={narrativeTone === 'provocative'}
                onChange={(e) => setNarrativeTone(e.target.value)}
              />
              <span>Provocative and bold</span>
            </label>
          </div>
          {errors.narrativeTone && <span className="error">{errors.narrativeTone}</span>}
        </div>

        {/* Question 5 */}
        <div className="question">
          <label>5. Anything you're particularly curious about?</label>
          <textarea
            placeholder="e.g. what drives the guest's thinking or how this connects to current trends"
            value={curiosityFocus}
            onChange={(e) => setCuriosityFocus(e.target.value)}
            className="text-input"
          />
          <small className="hint">Optional — helps steer the briefing toward your interests</small>
        </div>

        <div className="actions">
          <button onClick={onCancel} className="btn-cancel">
            ← Back
          </button>
          <button onClick={handleGenerate} className="btn-generate">
            GO!
          </button>
        </div>
      </div>
    </div>
  );
}
