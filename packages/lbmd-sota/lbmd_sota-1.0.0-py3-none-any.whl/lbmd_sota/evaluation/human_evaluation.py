"""
Human evaluation framework for LBMD interpretability studies.

This module addresses the critical feedback about missing human evaluation
by providing a comprehensive framework for validating interpretability claims
through human studies.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass
import json
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import random

@dataclass
class EvaluationTask:
    """Container for a single human evaluation task."""
    task_id: str
    image_path: str
    ground_truth_boundaries: np.ndarray
    lbmd_explanation: Dict[str, Any]
    baseline_explanations: Dict[str, Any]
    question: str
    expected_answer: str
    difficulty: str  # 'easy', 'medium', 'hard'
    category: str  # 'boundary_detection', 'object_segmentation', 'feature_importance'

@dataclass
class ParticipantResponse:
    """Container for a participant's response to an evaluation task."""
    participant_id: str
    task_id: str
    response: str
    confidence: int  # 1-5 scale
    time_taken: float  # seconds
    explanation_quality: int  # 1-5 scale
    preference: str  # 'lbmd', 'baseline', 'neither'
    comments: str

class HumanEvaluationStudy:
    """
    Comprehensive human evaluation framework for LBMD interpretability.
    
    This addresses the critical feedback about missing human evaluation
    by providing a systematic framework for validating interpretability claims.
    """
    
    def __init__(self, study_name: str = "LBMD_Interpretability_Study"):
        """
        Initialize human evaluation study.
        
        Args:
            study_name: Name of the study for organization
        """
        self.study_name = study_name
        self.tasks: List[EvaluationTask] = []
        self.responses: List[ParticipantResponse] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Study configuration
        self.n_participants_target = 20
        self.n_tasks_per_participant = 10
        self.categories = [
            'boundary_detection',
            'object_segmentation', 
            'feature_importance',
            'architectural_comparison'
        ]
        
    def create_evaluation_tasks(self, 
                              lbmd_results: List[Dict[str, Any]],
                              baseline_results: List[Dict[str, Any]],
                              images: List[np.ndarray]) -> List[EvaluationTask]:
        """
        Create evaluation tasks from LBMD and baseline results.
        
        Args:
            lbmd_results: List of LBMD analysis results
            baseline_results: List of baseline method results
            images: List of corresponding images
            
        Returns:
            List of evaluation tasks
        """
        tasks = []
        
        for i, (lbmd_result, baseline_result, image) in enumerate(zip(lbmd_results, baseline_results, images)):
            # Create different types of tasks
            task_types = self._create_task_types(lbmd_result, baseline_result, image, i)
            tasks.extend(task_types)
        
        # Randomize task order
        random.shuffle(tasks)
        
        self.tasks = tasks
        return tasks
    
    def _create_task_types(self, 
                          lbmd_result: Dict[str, Any],
                          baseline_result: Dict[str, Any],
                          image: np.ndarray,
                          task_id: int) -> List[EvaluationTask]:
        """Create different types of evaluation tasks."""
        tasks = []
        
        # Task 1: Boundary Detection
        if 'boundary_indices' in lbmd_result and 'boundary_indices' in baseline_result:
            task = EvaluationTask(
                task_id=f"boundary_{task_id}",
                image_path=f"image_{task_id}.png",
                ground_truth_boundaries=self._create_ground_truth_boundaries(image),
                lbmd_explanation=lbmd_result,
                baseline_explanations={'gradcam': baseline_result},
                question="Which method better identifies object boundaries?",
                expected_answer="lbmd",
                difficulty="medium",
                category="boundary_detection"
            )
            tasks.append(task)
        
        # Task 2: Object Segmentation
        if 'manifold_embedding' in lbmd_result:
            task = EvaluationTask(
                task_id=f"segmentation_{task_id}",
                image_path=f"image_{task_id}.png",
                ground_truth_boundaries=self._create_ground_truth_boundaries(image),
                lbmd_explanation=lbmd_result,
                baseline_explanations={'lime': baseline_result},
                question="Which explanation better shows how the model segments objects?",
                expected_answer="lbmd",
                difficulty="hard",
                category="object_segmentation"
            )
            tasks.append(task)
        
        # Task 3: Feature Importance
        if 'boundary_strength' in lbmd_result:
            task = EvaluationTask(
                task_id=f"features_{task_id}",
                image_path=f"image_{task_id}.png",
                ground_truth_boundaries=self._create_ground_truth_boundaries(image),
                lbmd_explanation=lbmd_result,
                baseline_explanations={'shap': baseline_result},
                question="Which method better highlights important features for the model's decision?",
                expected_answer="lbmd",
                difficulty="easy",
                category="feature_importance"
            )
            tasks.append(task)
        
        return tasks
    
    def _create_ground_truth_boundaries(self, image: np.ndarray) -> np.ndarray:
        """Create ground truth boundaries for evaluation."""
        # This would typically use actual ground truth data
        # For now, create synthetic boundaries for demonstration
        h, w = image.shape[:2]
        boundaries = np.zeros((h, w), dtype=bool)
        
        # Create some synthetic boundary regions
        for i in range(0, h, h//4):
            for j in range(0, w, w//4):
                if i < h-10 and j < w-10:
                    boundaries[i:i+10, j:j+10] = True
        
        return boundaries
    
    def create_evaluation_interface(self, output_dir: str = "human_evaluation") -> str:
        """
        Create HTML-based evaluation interface.
        
        Args:
            output_dir: Directory to save evaluation interface
            
        Returns:
            Path to the evaluation interface
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create HTML interface
        html_content = self._generate_html_interface()
        
        interface_path = output_path / "evaluation_interface.html"
        with open(interface_path, 'w') as f:
            f.write(html_content)
        
        # Create JavaScript for interaction
        js_content = self._generate_javascript()
        js_path = output_path / "evaluation.js"
        with open(js_path, 'w') as f:
            f.write(js_content)
        
        # Create CSS for styling
        css_content = self._generate_css()
        css_path = output_path / "evaluation.css"
        with open(css_path, 'w') as f:
            f.write(css_content)
        
        self.logger.info(f"Evaluation interface created at {interface_path}")
        return str(interface_path)
    
    def _generate_html_interface(self) -> str:
        """Generate HTML interface for human evaluation."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LBMD Interpretability Evaluation Study</title>
    <link rel="stylesheet" href="evaluation.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>LBMD Interpretability Evaluation Study</h1>
            <p>Thank you for participating in our study. Your responses will help us evaluate the interpretability of our method.</p>
        </header>
        
        <div id="participant-info">
            <h2>Participant Information</h2>
            <form id="participant-form">
                <label for="participant-id">Participant ID:</label>
                <input type="text" id="participant-id" required>
                
                <label for="expertise">ML/AI Expertise Level:</label>
                <select id="expertise" required>
                    <option value="beginner">Beginner (0-1 years)</option>
                    <option value="intermediate">Intermediate (2-5 years)</option>
                    <option value="advanced">Advanced (5+ years)</option>
                    <option value="expert">Expert (10+ years)</option>
                </select>
                
                <label for="background">Background:</label>
                <select id="background" required>
                    <option value="researcher">Researcher</option>
                    <option value="practitioner">Practitioner</option>
                    <option value="student">Student</option>
                    <option value="other">Other</option>
                </select>
                
                <button type="button" onclick="startEvaluation()">Start Evaluation</button>
            </form>
        </div>
        
        <div id="evaluation-tasks" style="display: none;">
            <div id="task-container">
                <h2>Task <span id="task-number">1</span> of <span id="total-tasks">10</span></h2>
                
                <div class="task-content">
                    <div class="image-container">
                        <h3>Original Image</h3>
                        <img id="original-image" src="" alt="Original Image">
                    </div>
                    
                    <div class="explanations">
                        <div class="explanation-panel">
                            <h3>Method A (LBMD)</h3>
                            <img id="lbmd-explanation" src="" alt="LBMD Explanation">
                            <div class="explanation-details">
                                <p><strong>Boundary Strength:</strong> <span id="lbmd-boundary-strength">-</span></p>
                                <p><strong>Manifold Dimension:</strong> <span id="lbmd-manifold-dim">-</span></p>
                                <p><strong>Analysis Time:</strong> <span id="lbmd-time">-</span>s</p>
                            </div>
                        </div>
                        
                        <div class="explanation-panel">
                            <h3>Method B (Baseline)</h3>
                            <img id="baseline-explanation" src="" alt="Baseline Explanation">
                            <div class="explanation-details">
                                <p><strong>Method:</strong> <span id="baseline-method">-</span></p>
                                <p><strong>Confidence:</strong> <span id="baseline-confidence">-</span></p>
                                <p><strong>Analysis Time:</strong> <span id="baseline-time">-</span>s</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="question">
                        <h3 id="task-question">Which method better identifies object boundaries?</h3>
                    </div>
                    
                    <div class="response-form">
                        <div class="rating-section">
                            <label>Which method provides better explanations?</label>
                            <div class="radio-group">
                                <input type="radio" id="prefer-lbmd" name="preference" value="lbmd">
                                <label for="prefer-lbmd">Method A (LBMD)</label>
                                
                                <input type="radio" id="prefer-baseline" name="preference" value="baseline">
                                <label for="prefer-baseline">Method B (Baseline)</label>
                                
                                <input type="radio" id="prefer-neither" name="preference" value="neither">
                                <label for="prefer-neither">Neither / No clear preference</label>
                            </div>
                        </div>
                        
                        <div class="rating-section">
                            <label>Explanation Quality (1-5 scale):</label>
                            <div class="rating-scale">
                                <input type="radio" id="quality-1" name="quality" value="1">
                                <label for="quality-1">1 (Poor)</label>
                                
                                <input type="radio" id="quality-2" name="quality" value="2">
                                <label for="quality-2">2</label>
                                
                                <input type="radio" id="quality-3" name="quality" value="3">
                                <label for="quality-3">3 (Average)</label>
                                
                                <input type="radio" id="quality-4" name="quality" value="4">
                                <label for="quality-4">4</label>
                                
                                <input type="radio" id="quality-5" name="quality" value="5">
                                <label for="quality-5">5 (Excellent)</label>
                            </div>
                        </div>
                        
                        <div class="rating-section">
                            <label>Confidence in your assessment (1-5 scale):</label>
                            <div class="rating-scale">
                                <input type="radio" id="confidence-1" name="confidence" value="1">
                                <label for="confidence-1">1 (Not confident)</label>
                                
                                <input type="radio" id="confidence-2" name="confidence" value="2">
                                <label for="confidence-2">2</label>
                                
                                <input type="radio" id="confidence-3" name="confidence" value="3">
                                <label for="confidence-3">3 (Moderately confident)</label>
                                
                                <input type="radio" id="confidence-4" name="confidence" value="4">
                                <label for="confidence-4">4</label>
                                
                                <input type="radio" id="confidence-5" name="confidence" value="5">
                                <label for="confidence-5">5 (Very confident)</label>
                            </div>
                        </div>
                        
                        <div class="comments-section">
                            <label for="comments">Additional comments (optional):</label>
                            <textarea id="comments" rows="3" placeholder="Please share any additional thoughts about the explanations..."></textarea>
                        </div>
                        
                        <div class="navigation">
                            <button type="button" id="prev-task" onclick="previousTask()" disabled>Previous</button>
                            <button type="button" id="next-task" onclick="nextTask()">Next Task</button>
                            <button type="button" id="submit-evaluation" onclick="submitEvaluation()" style="display: none;">Submit Evaluation</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="completion-message" style="display: none;">
            <h2>Thank you for completing the evaluation!</h2>
            <p>Your responses have been recorded. The study results will be used to improve our interpretability methods.</p>
        </div>
    </div>
    
    <script src="evaluation.js"></script>
</body>
</html>
        """
    
    def _generate_javascript(self) -> str:
        """Generate JavaScript for the evaluation interface."""
        return """
// Evaluation study JavaScript
let currentTask = 0;
let totalTasks = 10;
let startTime = null;
let responses = [];

// Task data (would be loaded from server in real implementation)
const tasks = [
    // This would be populated with actual task data
];

function startEvaluation() {
    const participantId = document.getElementById('participant-id').value;
    const expertise = document.getElementById('expertise').value;
    const background = document.getElementById('background').value;
    
    if (!participantId) {
        alert('Please enter a participant ID');
        return;
    }
    
    // Hide participant info, show evaluation tasks
    document.getElementById('participant-info').style.display = 'none';
    document.getElementById('evaluation-tasks').style.display = 'block';
    
    startTime = Date.now();
    loadTask(0);
}

function loadTask(taskIndex) {
    if (taskIndex >= tasks.length) {
        showCompletionMessage();
        return;
    }
    
    const task = tasks[taskIndex];
    currentTask = taskIndex;
    
    // Update task number
    document.getElementById('task-number').textContent = taskIndex + 1;
    document.getElementById('total-tasks').textContent = tasks.length;
    
    // Load task content
    document.getElementById('task-question').textContent = task.question;
    
    // Update navigation buttons
    document.getElementById('prev-task').disabled = taskIndex === 0;
    document.getElementById('next-task').style.display = taskIndex < tasks.length - 1 ? 'block' : 'none';
    document.getElementById('submit-evaluation').style.display = taskIndex === tasks.length - 1 ? 'block' : 'none';
    
    // Clear previous responses
    clearForm();
}

function nextTask() {
    saveCurrentResponse();
    loadTask(currentTask + 1);
}

function previousTask() {
    saveCurrentResponse();
    loadTask(currentTask - 1);
}

function saveCurrentResponse() {
    const response = {
        taskId: tasks[currentTask].task_id,
        preference: document.querySelector('input[name="preference"]:checked')?.value || null,
        quality: document.querySelector('input[name="quality"]:checked')?.value || null,
        confidence: document.querySelector('input[name="confidence"]:checked')?.value || null,
        comments: document.getElementById('comments').value,
        timeTaken: (Date.now() - startTime) / 1000
    };
    
    responses.push(response);
}

function clearForm() {
    // Clear all form inputs
    document.querySelectorAll('input[type="radio"]').forEach(input => {
        input.checked = false;
    });
    document.getElementById('comments').value = '';
}

function submitEvaluation() {
    saveCurrentResponse();
    
    // Submit responses (would send to server in real implementation)
    console.log('Evaluation completed:', responses);
    
    // Show completion message
    showCompletionMessage();
}

function showCompletionMessage() {
    document.getElementById('evaluation-tasks').style.display = 'none';
    document.getElementById('completion-message').style.display = 'block';
}
        """
    
    def _generate_css(self) -> str:
        """Generate CSS for the evaluation interface."""
        return """
/* Evaluation Study CSS */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background-color: white;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

header {
    text-align: center;
    margin-bottom: 30px;
    border-bottom: 2px solid #eee;
    padding-bottom: 20px;
}

h1 {
    color: #333;
    margin-bottom: 10px;
}

h2 {
    color: #555;
    margin-top: 30px;
    margin-bottom: 15px;
}

h3 {
    color: #666;
    margin-bottom: 10px;
}

form {
    background-color: #f9f9f9;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
    color: #555;
}

input[type="text"], select, textarea {
    width: 100%;
    padding: 8px;
    margin-bottom: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-sizing: border-box;
}

button {
    background-color: #007bff;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    margin-right: 10px;
}

button:hover {
    background-color: #0056b3;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.task-content {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 20px;
    margin-bottom: 30px;
}

.image-container {
    text-align: center;
}

.image-container img {
    max-width: 100%;
    height: auto;
    border: 1px solid #ddd;
    border-radius: 5px;
}

.explanations {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.explanation-panel {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 15px;
    background-color: #f9f9f9;
}

.explanation-panel img {
    width: 100%;
    height: auto;
    margin-bottom: 10px;
    border: 1px solid #ccc;
    border-radius: 3px;
}

.explanation-details {
    font-size: 14px;
    color: #666;
}

.question {
    background-color: #e7f3ff;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
    border-left: 4px solid #007bff;
}

.response-form {
    background-color: #f9f9f9;
    padding: 20px;
    border-radius: 5px;
}

.rating-section {
    margin-bottom: 20px;
    padding: 15px;
    background-color: white;
    border-radius: 5px;
    border: 1px solid #eee;
}

.radio-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 10px;
}

.radio-group input[type="radio"] {
    width: auto;
    margin-right: 8px;
}

.rating-scale {
    display: flex;
    gap: 15px;
    margin-top: 10px;
    flex-wrap: wrap;
}

.rating-scale input[type="radio"] {
    width: auto;
    margin-right: 5px;
}

.comments-section {
    margin-top: 20px;
}

.comments-section textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    resize: vertical;
}

.navigation {
    text-align: center;
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #eee;
}

#completion-message {
    text-align: center;
    padding: 50px;
    background-color: #d4edda;
    border-radius: 5px;
    border: 1px solid #c3e6cb;
}

@media (max-width: 768px) {
    .task-content {
        grid-template-columns: 1fr;
    }
    
    .explanations {
        grid-template-columns: 1fr;
    }
    
    .rating-scale {
        flex-direction: column;
    }
}
        """
    
    def analyze_responses(self) -> Dict[str, Any]:
        """
        Analyze human evaluation responses.
        
        Returns:
            Comprehensive analysis of human evaluation results
        """
        if not self.responses:
            return {'error': 'No responses to analyze'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(self.responses)
        
        # Basic statistics
        analysis = {
            'total_responses': len(df),
            'participant_count': df['participant_id'].nunique(),
            'task_completion_rate': len(df) / (self.n_participants_target * self.n_tasks_per_participant),
        }
        
        # Preference analysis
        preference_counts = df['preference'].value_counts()
        analysis['preference_analysis'] = {
            'lbmd_preference': preference_counts.get('lbmd', 0) / len(df),
            'baseline_preference': preference_counts.get('baseline', 0) / len(df),
            'neither_preference': preference_counts.get('neither', 0) / len(df)
        }
        
        # Quality ratings
        quality_ratings = df['quality'].dropna().astype(int)
        analysis['quality_analysis'] = {
            'mean_quality': float(quality_ratings.mean()),
            'std_quality': float(quality_ratings.std()),
            'quality_distribution': quality_ratings.value_counts().to_dict()
        }
        
        # Confidence analysis
        confidence_ratings = df['confidence'].dropna().astype(int)
        analysis['confidence_analysis'] = {
            'mean_confidence': float(confidence_ratings.mean()),
            'std_confidence': float(confidence_ratings.std()),
            'confidence_distribution': confidence_ratings.value_counts().to_dict()
        }
        
        # Statistical significance tests
        from scipy import stats
        
        # Test if LBMD preference is significantly different from random
        lbmd_preference_rate = analysis['preference_analysis']['lbmd_preference']
        n_responses = len(df)
        p_value = stats.binom_test(
            int(lbmd_preference_rate * n_responses), 
            n_responses, 
            0.33  # Expected if random choice between 3 options
        )
        
        analysis['statistical_tests'] = {
            'lbmd_preference_significance': {
                'p_value': p_value,
                'is_significant': p_value < 0.05,
                'effect_size': lbmd_preference_rate - 0.33
            }
        }
        
        # Task difficulty analysis
        if 'task_id' in df.columns:
            task_analysis = df.groupby('task_id').agg({
                'preference': lambda x: (x == 'lbmd').mean(),
                'quality': lambda x: x.dropna().astype(int).mean(),
                'confidence': lambda x: x.dropna().astype(int).mean()
            }).to_dict('index')
            analysis['task_analysis'] = task_analysis
        
        return analysis
    
    def generate_evaluation_report(self, output_path: str = "human_evaluation_report.json") -> str:
        """
        Generate comprehensive human evaluation report.
        
        Args:
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        analysis = self.analyze_responses()
        
        # Add metadata
        report = {
            'study_metadata': {
                'study_name': self.study_name,
                'generation_time': datetime.now().isoformat(),
                'total_tasks': len(self.tasks),
                'total_responses': len(self.responses)
            },
            'analysis_results': analysis
        }
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Human evaluation report saved to {output_path}")
        return output_path

def create_human_evaluation_study(lbmd_results: List[Dict[str, Any]],
                                baseline_results: List[Dict[str, Any]],
                                images: List[np.ndarray],
                                output_dir: str = "human_evaluation") -> HumanEvaluationStudy:
    """
    Create and configure a human evaluation study.
    
    Args:
        lbmd_results: LBMD analysis results
        baseline_results: Baseline method results
        images: Corresponding images
        output_dir: Output directory for study materials
        
    Returns:
        Configured human evaluation study
    """
    study = HumanEvaluationStudy()
    
    # Create evaluation tasks
    tasks = study.create_evaluation_tasks(lbmd_results, baseline_results, images)
    
    # Create evaluation interface
    interface_path = study.create_evaluation_interface(output_dir)
    
    print(f"Human evaluation study created:")
    print(f"- {len(tasks)} evaluation tasks")
    print(f"- Interface available at: {interface_path}")
    print(f"- Target participants: {study.n_participants_target}")
    print(f"- Tasks per participant: {study.n_tasks_per_participant}")
    
    return study
