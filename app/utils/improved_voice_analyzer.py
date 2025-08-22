#!/usr/bin/env python3
"""
Improved audio-based voice analyzer.
Focuses on meaningful audio patterns and conversation flow.
"""

import librosa
import numpy as np
import matplotlib.pyplot as plt
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ImprovedVoiceAnalyzer:
    def __init__(self, audio_path: str, transcript_path: str = None, sample_rate: int = 16000, 
                 pause_sensitivity: str = "normal"):
        """
        Initialize improved voice analyzer.
        
        Args:
            audio_path: Path to audio file
            transcript_path: Path to JSON transcript file (optional - for enhanced analysis)
            sample_rate: Target sample rate for analysis
            pause_sensitivity: Pause detection sensitivity ("low", "normal", "high")
        """
        self.audio_path = audio_path
        self.transcript_path = transcript_path
        self.sample_rate = sample_rate
        self.pause_sensitivity = pause_sensitivity
        
        # Set pause detection thresholds based on sensitivity
        if pause_sensitivity == "low":
            self.min_pause_duration = 6.0  # Only flag very long pauses
            self.long_pause_threshold = 10.0
            self.medium_pause_threshold = 7.0
        elif pause_sensitivity == "high":
            self.min_pause_duration = 2.0  # Flag even short gaps
            self.long_pause_threshold = 5.0
            self.medium_pause_threshold = 3.0
        else:  # "normal"
            self.min_pause_duration = 4.0  # Balanced sensitivity
            self.long_pause_threshold = 7.0
            self.medium_pause_threshold = 5.0
        
        # Load audio
        self.audio, self.sr = librosa.load(audio_path, sr=sample_rate)
        self.duration = len(self.audio) / self.sr
        
        # Initialize transcript data (optional)
        self.transcript_data = None
        self.conversation_timeline = []
        
        # Load transcript if provided
        if transcript_path and Path(transcript_path).exists():
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    self.transcript_data = json.load(f)
                # Parse transcript timeline
                self.conversation_timeline = self._parse_transcript_timeline()
                print(f"Loaded: {Path(audio_path).name}")
                print(f"Duration: {self.duration:.2f}s")
                print(f"Transcript events: {len(self.conversation_timeline)}")
            except Exception as e:
                print(f"Warning: Could not load transcript: {e}")
                print(f"Continuing with audio-only analysis...")
        else:
            print(f"Loaded: {Path(audio_path).name}")
            print(f"Duration: {self.duration:.2f}s")
            print(f"Running audio-only analysis (no transcript)")
    
    def _parse_transcript_timeline(self) -> List[Dict]:
        """Parse JSON transcript into timeline with calculated durations."""
        turns = self.transcript_data['turns']
        timeline = []
        
        for i, turn in enumerate(turns):
            # Parse timestamp
            timestamp = datetime.fromisoformat(turn['timestamp'].replace('Z', '+00:00'))
            
            # Calculate relative time from first turn
            if i == 0:
                self.start_time = timestamp
                relative_time = 0.0
            else:
                relative_time = (timestamp - self.start_time).total_seconds()
            
            # Estimate turn duration (until next turn or end)
            if i < len(turns) - 1:
                next_timestamp = datetime.fromisoformat(turns[i + 1]['timestamp'].replace('Z', '+00:00'))
                duration = (next_timestamp - timestamp).total_seconds()
            else:
                duration = 1.0  # Default for last turn
            
            timeline.append({
                'turn_id': i,
                'role': turn['role'],
                'content': turn['content'],
                'start_time': relative_time,
                'end_time': relative_time + duration,
                'duration': duration,
                'timestamp': timestamp
            })
        
        return timeline
    
    def detect_speech_segments(self) -> List[Dict]:
        """
        Detect actual speech segments using improved voice activity detection.
        Uses multiple methods for more accurate speech detection.
        """
        # Use librosa's onset detection for speech boundaries
        hop_length = 512
        frame_length = 2048
        
        # Method 1: Spectral rolloff with better threshold
        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=self.audio,
            sr=self.sr,
            hop_length=hop_length
        )[0]
        
        # Use balanced thresholds - not too aggressive, not too conservative
        speech_threshold = np.percentile(spectral_rolloff, 25)  # Bottom 25% is silence
        speech_mask_1 = spectral_rolloff > speech_threshold
        
        # Method 2: RMS energy for additional validation
        rms_energy = librosa.feature.rms(y=self.audio, hop_length=hop_length)[0]
        energy_threshold = np.percentile(rms_energy, 30)  # Bottom 30% is silence
        speech_mask_2 = rms_energy > energy_threshold
        
        # Method 3: Zero crossing rate for speech-like characteristics
        zcr = librosa.feature.zero_crossing_rate(y=self.audio, hop_length=hop_length)[0]
        zcr_threshold = np.percentile(zcr, 35)  # Bottom 35% is silence
        speech_mask_3 = zcr > zcr_threshold
        
        # Combine methods - require at least 2 out of 3 methods to agree
        # This balances false positives and false negatives
        vote_count = speech_mask_1.astype(int) + speech_mask_2.astype(int) + speech_mask_3.astype(int)
        combined_speech_mask = vote_count >= 2  # Majority vote
        
        # Apply smoothing to reduce rapid switching
        from scipy.ndimage import binary_closing, binary_opening
        combined_speech_mask = binary_closing(combined_speech_mask, structure=np.ones(3))
        combined_speech_mask = binary_opening(combined_speech_mask, structure=np.ones(2))
        
        times = librosa.frames_to_time(
            np.arange(len(combined_speech_mask)),
            sr=self.sr,
            hop_length=hop_length
        )
        
        # Find continuous speech segments with improved logic
        speech_segments = []
        in_speech = False
        segment_start = 0
        
        for i, (time, is_speech) in enumerate(zip(times, combined_speech_mask)):
            if is_speech and not in_speech:
                # Start of speech segment
                segment_start = time
                in_speech = True
            elif not is_speech and in_speech:
                # End of speech segment
                if time - segment_start > 0.2:  # Reduced minimum to 200ms for better detection
                    speech_segments.append({
                        'start': segment_start,
                        'end': time,
                        'duration': time - segment_start
                    })
                in_speech = False
        
        # Handle case where audio ends during speech
        if in_speech and len(times) > 0:
            speech_segments.append({
                'start': segment_start,
                'end': times[-1],
                'duration': times[-1] - segment_start
            })
        
        # Merge only very close segments (likely same speech interrupted by brief noise)
        merged_segments = []
        if speech_segments:
            current_segment = speech_segments[0].copy()
            
            for next_segment in speech_segments[1:]:
                gap = next_segment['start'] - current_segment['end']
                
                # Only merge if gap is extremely small (< 0.2s) - preserve natural pauses
                if gap < 0.2:
                    current_segment['end'] = next_segment['end']
                    current_segment['duration'] = current_segment['end'] - current_segment['start']
                else:
                    merged_segments.append(current_segment)
                    current_segment = next_segment.copy()
            
            merged_segments.append(current_segment)
        
        return merged_segments if merged_segments else speech_segments
    
    def detect_pauses(self, min_pause_duration: float = None) -> List[Dict]:
        """
        Detect meaningful pauses in conversation flow.
        Focus on pauses between actual speech segments.
        Uses configurable sensitivity for natural conversation.
        """
        # Use instance threshold if not specified
        if min_pause_duration is None:
            min_pause_duration = self.min_pause_duration
            
        pauses = []
        speech_segments = self.detect_speech_segments()
        
        # Method 1: Gaps between speech segments (primary method)
        for i in range(len(speech_segments) - 1):
            current_segment = speech_segments[i]
            next_segment = speech_segments[i + 1]
            
            gap_duration = next_segment['start'] - current_segment['end']
            
            if gap_duration >= min_pause_duration:
                # Classify pause based on configurable thresholds
                if gap_duration > self.long_pause_threshold:
                    pause_type = 'long_pause'
                    severity = 'high'
                elif gap_duration > self.medium_pause_threshold:
                    pause_type = 'medium_pause'
                    severity = 'medium'
                else:
                    pause_type = 'short_pause'
                    severity = 'low'
                
                pauses.append({
                    'start_time': current_segment['end'],
                    'end_time': next_segment['start'],
                    'duration': gap_duration,
                    'type': pause_type,
                    'severity': severity
                })
        
        # Method 2: Enhanced pause detection using energy analysis
        if len(speech_segments) > 0:
            # Analyze energy patterns around speech segments
            enhanced_pauses = self._detect_enhanced_pauses(speech_segments, min_pause_duration)
            pauses.extend(enhanced_pauses)
        
        # Method 3: Transcript-based analysis (if available)
        if self.conversation_timeline:
            transcript_pauses = self._detect_transcript_based_pauses(min_pause_duration)
            pauses.extend(transcript_pauses)
        
        # Remove duplicates and sort by time
        unique_pauses = self._deduplicate_pauses(pauses)
        return sorted(unique_pauses, key=lambda x: x['start_time'])
    
    def _detect_enhanced_pauses(self, speech_segments: List[Dict], min_pause_duration: float) -> List[Dict]:
        """Enhanced pause detection using energy analysis around speech segments."""
        enhanced_pauses = []
        
        if len(speech_segments) < 2:
            return enhanced_pauses
        
        # Analyze energy patterns around speech boundaries
        hop_length = 512
        rms_energy = librosa.feature.rms(y=self.audio, hop_length=hop_length)[0]
        energy_times = librosa.frames_to_time(np.arange(len(rms_energy)), sr=self.sr, hop_length=hop_length)
        
        for i in range(len(speech_segments) - 1):
            current_segment = speech_segments[i]
            next_segment = speech_segments[i + 1]
            
            # Look for energy drops in the gap
            gap_start = current_segment['end']
            gap_end = next_segment['start']
            gap_duration = gap_end - gap_start
            
            if gap_duration >= min_pause_duration:
                # Find energy frames in the gap
                gap_start_frame = np.argmin(np.abs(energy_times - gap_start))
                gap_end_frame = np.argmin(np.abs(energy_times - gap_end))
                
                if gap_start_frame < gap_end_frame and gap_start_frame < len(rms_energy):
                    gap_energies = rms_energy[gap_start_frame:gap_end_frame]
                    
                    # Check if there's a significant energy drop (indicating silence)
                    if len(gap_energies) > 0:
                        energy_drop = np.max(gap_energies) - np.min(gap_energies)
                        energy_threshold = np.percentile(rms_energy, 70)
                        
                        if energy_drop > energy_threshold * 0.5:  # Significant energy variation
                            enhanced_pauses.append({
                                'start_time': gap_start,
                                'end_time': gap_end,
                                'duration': gap_duration,
                                'type': 'enhanced_speech_gap',
                                'severity': 'high' if gap_duration > 5.0 else 'medium',
                                'confidence': min(1.0, energy_drop / energy_threshold)
                            })
        
        return enhanced_pauses
    
    def _detect_transcript_based_pauses(self, min_pause_duration: float) -> List[Dict]:
        """Detect pauses based on transcript timing (if available)."""
        transcript_pauses = []
        
        if not self.conversation_timeline:
            return transcript_pauses
        
        conversation_turns = [t for t in self.conversation_timeline 
                            if 'session' not in t['content'].lower()]
        
        for i in range(len(conversation_turns) - 1):
            current_turn = conversation_turns[i]
            next_turn = conversation_turns[i + 1]
            
            gap = next_turn['start_time'] - current_turn['end_time']
            
            if gap >= min_pause_duration:
                # Check if this is an agent delay
                is_agent_delay = (
                    current_turn['role'] == 'USER' and 
                    next_turn['role'] in ['AGENT_SPEECH', 'AGENT']
                )
                
                pause_type = 'agent_delay' if is_agent_delay else 'conversation_pause'
                
                transcript_pauses.append({
                    'start_time': current_turn['end_time'],
                    'end_time': next_turn['start_time'],
                    'duration': gap,
                    'type': pause_type,
                    'severity': 'high' if gap > 5.0 else 'medium',
                    'context': {
                        'after_role': current_turn['role'],
                        'before_role': next_turn['role'],
                        'previous_content': current_turn['content'],
                        'next_content': next_turn['content']
                    }
                })
        
        return transcript_pauses
    
    def _deduplicate_pauses(self, pauses: List[Dict]) -> List[Dict]:
        """Remove duplicate or overlapping pauses."""
        unique_pauses = []
        
        for pause in pauses:
            # Check if this pause overlaps with existing ones
            is_duplicate = False
            for existing in unique_pauses:
                if (abs(pause['start_time'] - existing['start_time']) < 0.5 and
                    abs(pause['duration'] - existing['duration']) < 0.5):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_pauses.append(pause)
        
        return unique_pauses
    
    def detect_interruptions(self) -> List[Dict]:
        """
        Detect interruptions based on audio analysis and optional transcript data.
        Focus on rapid speech transitions and energy patterns.
        """
        interruptions = []
        
        # Method 1: Audio-based interruption detection
        audio_interruptions = self._detect_audio_interruptions()
        interruptions.extend(audio_interruptions)
        
        # Method 2: Transcript-based detection (if available)
        if self.conversation_timeline:
            transcript_interruptions = self._detect_transcript_interruptions()
            interruptions.extend(transcript_interruptions)
        
        # Remove duplicates and sort by time
        unique_interruptions = self._deduplicate_interruptions(interruptions)
        return sorted(unique_interruptions, key=lambda x: x['time'])
    
    def _detect_audio_interruptions(self) -> List[Dict]:
        """Detect interruptions using audio analysis only."""
        interruptions = []
        speech_segments = self.detect_speech_segments()
        
        if len(speech_segments) < 2:
            return interruptions
        
        # Analyze gaps between speech segments
        for i in range(len(speech_segments) - 1):
            current_segment = speech_segments[i]
            next_segment = speech_segments[i + 1]
            
            gap = next_segment['start'] - current_segment['end']
            
            # Very short gaps suggest interruptions
            if gap < 0.3:  # Less than 300ms
                # Analyze energy patterns around the gap
                hop_length = 512
                rms_energy = librosa.feature.rms(y=self.audio, hop_length=hop_length)[0]
                energy_times = librosa.frames_to_time(np.arange(len(rms_energy)), sr=self.sr, hop_length=hop_length)
                
                # Find energy frames around the gap
                gap_start_frame = np.argmin(np.abs(energy_times - current_segment['end']))
                gap_end_frame = np.argmin(np.abs(energy_times - next_segment['start']))
                
                if gap_start_frame < gap_end_frame and gap_start_frame < len(rms_energy):
                    # Check for energy spikes indicating overlapping speech
                    gap_energies = rms_energy[gap_start_frame:gap_end_frame]
                    
                    if len(gap_energies) > 0:
                        energy_variance = np.var(gap_energies)
                        energy_threshold = np.percentile(rms_energy, 80)
                        
                        if energy_variance > energy_threshold * 0.3:  # High energy variation
                            interruption_type = 'audio_overlap'
                            confidence = min(1.0, energy_variance / energy_threshold)
                            
                            interruptions.append({
                                'time': next_segment['start'],
                                'gap_duration': gap,
                                'type': interruption_type,
                                'confidence': confidence,
                                'severity': 'high' if gap < 0.1 else 'medium'
                            })
        
        return interruptions
    
    def _detect_transcript_interruptions(self) -> List[Dict]:
        """Detect interruptions based on transcript timing (if available)."""
        transcript_interruptions = []
        conversation_turns = [t for t in self.conversation_timeline 
                            if 'session' not in t['content'].lower()]
        
        for i in range(len(conversation_turns) - 1):
            current_turn = conversation_turns[i]
            next_turn = conversation_turns[i + 1]
            
            gap = next_turn['start_time'] - current_turn['end_time']
            
            if gap < 0.5:  # Less than 500ms
                interruption_type = 'rapid_response'
                confidence = max(0.2, 1.0 - (gap * 2))
                
                # Classify based on roles
                if current_turn['role'] == 'USER' and next_turn['role'] == 'AGENT_SPEECH':
                    if gap < 0.1:
                        interruption_type = 'agent_interrupts_user'
                        confidence = 0.8
                    else:
                        continue
                elif current_turn['role'] == 'AGENT_SPEECH' and next_turn['role'] == 'USER':
                    interruption_type = 'user_interrupts_agent'
                    confidence = 0.7
                elif gap < 0.05:
                    interruption_type = 'system_overlap'
                    confidence = 0.9
                else:
                    continue
                
                transcript_interruptions.append({
                    'time': next_turn['start_time'],
                    'gap_duration': gap,
                    'type': interruption_type,
                    'confidence': confidence,
                    'context': {
                        'interrupted_role': current_turn['role'],
                        'interrupting_role': next_turn['role']
                    }
                })
        
        return transcript_interruptions
    
    def _deduplicate_interruptions(self, interruptions: List[Dict]) -> List[Dict]:
        """Remove duplicate or overlapping interruptions."""
        unique_interruptions = []
        
        for interruption in interruptions:
            is_duplicate = False
            for existing in unique_interruptions:
                if abs(interruption['time'] - existing['time']) < 0.1:  # Within 100ms
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_interruptions.append(interruption)
        
        return unique_interruptions
    
    def detect_call_termination_issues(self) -> Dict[str, Any]:
        """
        Analyze call termination patterns for issues.
        Focus on audio patterns and optional transcript data.
        """
        termination_analysis = {
            'session_started_properly': False,
            'session_ended_properly': False,
            'abrupt_ending': False,
            'duplicate_endings': False,
            'last_speaker_was_user': False,
            'issues': []
        }
        
        # Audio-based termination analysis (primary method)
        speech_segments = self.detect_speech_segments()
        if speech_segments:
            last_speech_end = speech_segments[-1]['end']
            silence_at_end = self.duration - last_speech_end
            
            # Analyze ending patterns
            if silence_at_end > 10.0:
                termination_analysis['issues'].append(f'Very long silence at end ({silence_at_end:.1f}s)')
            elif silence_at_end > 5.0:
                termination_analysis['issues'].append(f'Long silence at end ({silence_at_end:.1f}s)')
            elif silence_at_end < 0.2:
                termination_analysis['abrupt_ending'] = True
                termination_analysis['issues'].append('Very abrupt audio ending - possible cutoff')
            
            # Check for natural fade vs abrupt cut
            if silence_at_end < 1.0 and len(speech_segments) > 0:
                # Analyze the last speech segment
                last_segment = speech_segments[-1]
                last_segment_duration = last_segment['duration']
                
                if last_segment_duration < 0.5:  # Very short last segment
                    termination_analysis['abrupt_ending'] = True
                    termination_analysis['issues'].append('Last speech segment very short - possible cutoff')
        
        # Transcript-based analysis (if available)
        if self.conversation_timeline:
            transcript_analysis = self._analyze_transcript_termination()
            termination_analysis.update(transcript_analysis)
        
        return termination_analysis
    
    def _analyze_transcript_termination(self) -> Dict[str, Any]:
        """Analyze termination using transcript data (if available)."""
        transcript_analysis = {
            'session_started_properly': False,
            'session_ended_properly': False,
            'duplicate_endings': False,
            'last_speaker_was_user': False
        }
        
        if not self.conversation_timeline:
            return transcript_analysis
        
        # Check for session start
        first_turn = self.conversation_timeline[0]
        if 'session started' in first_turn['content'].lower():
            transcript_analysis['session_started_properly'] = True
        
        # Count session end messages
        session_end_count = sum(1 for turn in self.conversation_timeline 
                               if 'session ended' in turn['content'].lower())
        
        if session_end_count > 0:
            transcript_analysis['session_ended_properly'] = True
        
        if session_end_count > 1:
            transcript_analysis['duplicate_endings'] = True
        
        # Conversation flow analysis
        conversation_turns = [t for t in self.conversation_timeline 
                            if 'session' not in t['content'].lower()]
        
        if conversation_turns:
            last_conversation = conversation_turns[-1]
            if last_conversation['role'] == 'USER':
                transcript_analysis['last_speaker_was_user'] = True
        
        return transcript_analysis
    
    def analyze_conversation(self) -> Dict[str, Any]:
        """
        Run comprehensive conversation analysis.
        """
        print("\nAnalyzing audio and conversation flow...")
        
        # Detect speech segments
        speech_segments = self.detect_speech_segments()
        total_speech_time = sum(seg['duration'] for seg in speech_segments)
        speech_percentage = (total_speech_time / self.duration) * 100
        
        # Run analyses
        pauses = self.detect_pauses()
        interruptions = self.detect_interruptions()
        termination = self.detect_call_termination_issues()
        
        # Filter conversation turns
        conversation_turns = [t for t in self.conversation_timeline 
                            if 'session' not in t['content'].lower()]
        
        results = {
            'audio_info': {
                'file': Path(self.audio_path).name,
                'duration': self.duration,
                'speech_time': total_speech_time,
                'speech_percentage': speech_percentage
            },
            'speech_segments': speech_segments,
            'conversation_timeline': conversation_turns,
            'pauses': pauses,
            'interruptions': interruptions,
            'termination': termination,
            'summary': {
                'pause_count': len(pauses),
                'agent_delay_count': len([p for p in pauses if p.get('type') == 'agent_delay']),
                'interruption_count': len(interruptions),
                'termination_issues': len(termination['issues']),
                'conversation_health_score': self._calculate_health_score(pauses, interruptions, termination)
            }
        }
        
        return results
    
    def _calculate_health_score(self, pauses, interruptions, termination) -> float:
        """Calculate conversation health score (0-100)."""
        base_score = 100
        
        # Deduct points for real issues
        agent_delays = [p for p in pauses if p.get('type') == 'agent_delay']
        base_score -= len(agent_delays) * 15  # Agent delays are serious
        base_score -= len(pauses) * 5  # General pauses
        base_score -= len(interruptions) * 10  # Real interruptions
        base_score -= len(termination['issues']) * 20  # Termination issues
        
        return max(0, base_score)
    
    def print_summary(self, results: Dict[str, Any]):
        """Print analysis summary."""
        print("\n" + "="*50)
        print("IMPROVED AUDIO ANALYSIS SUMMARY")
        print("="*50)
        
        audio_info = results['audio_info']
        print(f"File: {audio_info['file']}")
        print(f"Duration: {audio_info['duration']:.2f}s")
        print(f"Speech: {audio_info['speech_time']:.2f}s ({audio_info['speech_percentage']:.1f}%)")
        
        summary = results['summary']
        print(f"\nDetected Issues:")
        print(f"  Pauses: {summary['pause_count']}")
        print(f"  Agent delays: {summary['agent_delay_count']}")
        print(f"  Interruptions: {summary['interruption_count']}")
        print(f"  Termination issues: {summary['termination_issues']}")
        print(f"  Health score: {summary['conversation_health_score']:.0f}/100")
        
        # Show specific issues
        agent_delays = [p for p in results['pauses'] if p.get('type') == 'agent_delay']
        if agent_delays:
            print(f"\nAgent delays:")
            for delay in agent_delays[:3]:
                print(f"  {delay['duration']:.1f}s after: '{delay['context']['previous_content']}'")
        
        if results['pauses'] and not agent_delays:
            print(f"\nPauses detected:")
            for pause in results['pauses'][:3]:
                print(f"  {pause['duration']:.1f}s pause at {pause['start_time']:.1f}s")
        
        if results['interruptions']:
            print(f"\nInterruptions:")
            for interruption in results['interruptions'][:3]:
                print(f"  {interruption['type']} at {interruption['time']:.1f}s")
        
        if results['termination']['issues']:
            print(f"\nTermination issues:")
            for issue in results['termination']['issues']:
                print(f"  {issue}")
        
        print("="*50)
    
    def visualize(self, results: Dict[str, Any], save_path: str = None):
        """Create visualization of the analysis."""
        fig, axes = plt.subplots(3, 1, figsize=(15, 10))
        
        # Plot 1: Audio waveform with speech segments
        times = np.linspace(0, self.duration, len(self.audio))
        axes[0].plot(times, self.audio, alpha=0.6, color='blue', linewidth=0.5)
        
        # Highlight speech segments
        for segment in results['speech_segments']:
            axes[0].axvspan(segment['start'], segment['end'], alpha=0.3, color='green', label='Speech')
        
        axes[0].set_title('Audio Waveform with Speech Detection')
        axes[0].set_ylabel('Amplitude')
        axes[0].set_xlim(0, self.duration)
        
        # Plot 2: Conversation timeline
        conversation_turns = results['conversation_timeline']
        y_positions = {'USER': 0, 'AGENT': 1, 'AGENT_SPEECH': 2}
        colors = {'USER': 'blue', 'AGENT': 'red', 'AGENT_SPEECH': 'orange'}
        
        for turn in conversation_turns:
            y_pos = y_positions.get(turn['role'], 0)
            axes[1].barh(y_pos, turn['duration'], left=turn['start_time'], 
                        color=colors.get(turn['role'], 'gray'), alpha=0.7)
        
        # Mark pauses
        for pause in results['pauses']:
            color = 'red' if pause.get('type') == 'agent_delay' else 'orange'
            axes[1].axvspan(pause['start_time'], pause['end_time'], alpha=0.5, color=color)
        
        # Mark interruptions
        for interruption in results['interruptions']:
            axes[1].axvline(x=interruption['time'], color='red', linestyle='--', alpha=0.8)
        
        axes[1].set_title('Conversation Timeline')
        axes[1].set_ylabel('Role')
        axes[1].set_yticks(list(y_positions.values()))
        axes[1].set_yticklabels(list(y_positions.keys()))
        axes[1].set_xlim(0, self.duration)
        
        # Plot 3: Issue summary
        issue_types = ['Pauses', 'Agent Delays', 'Interruptions', 'Termination Issues']
        issue_counts = [
            results['summary']['pause_count'],
            results['summary']['agent_delay_count'],
            results['summary']['interruption_count'],
            results['summary']['termination_issues']
        ]
        
        bars = axes[2].bar(issue_types, issue_counts, color=['orange', 'red', 'purple', 'brown'])
        axes[2].set_title('Issue Summary')
        axes[2].set_ylabel('Count')
        
        # Add count labels on bars
        for bar, count in zip(bars, issue_counts):
            if count > 0:
                axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           str(count), ha='center', va='bottom')
        
        axes[2].set_xlabel('Issue Type')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        else:
            plt.show()


def analyze_audio_conversation(audio_path: str, transcript_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Analyze audio conversation for meaningful issues.
    
    Args:
        audio_path: Path to audio file
        transcript_path: Path to transcript JSON
        output_dir: Directory to save outputs (optional)
    
    Returns:
        Analysis results
    """
    analyzer = ImprovedVoiceAnalyzer(audio_path, transcript_path)
    results = analyzer.analyze_conversation()
    analyzer.print_summary(results)
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        base_name = Path(audio_path).stem
        viz_path = output_path / f"{base_name}_improved_analysis.png"
        analyzer.visualize(results, save_path=str(viz_path))
    else:
        analyzer.visualize(results)
    
    return results
