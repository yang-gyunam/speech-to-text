<script lang="ts">
  import Icon from '../icons/Icon.svelte';
  import StageIndicator from '../processing/StageIndicator.svelte';
  import ProcessingLog from '../processing/ProcessingLog.svelte';
  import TimeEstimation from '../processing/TimeEstimation.svelte';
  import Button from '../ui/Button.svelte';
  import ProgressBar from '../ui/ProgressBar.svelte';

  interface LogEntry {
    id: string;
    timestamp: Date;
    level: 'info' | 'warning' | 'error' | 'success';
    message: string;
    details?: string;
  }

  interface Props {
    progress: any;
    currentFile?: string;
    onCancel?: () => void;
    onPause?: (() => void) | null;
    onResume?: (() => void) | null;
    isPaused?: boolean;
  }

  const {
    progress,
    currentFile = 'audio.m4a',
    onCancel = () => {},
    onPause = null,
    onResume = null,
    isPaused = false
  }: Props = $props();

  let logEntries = $state([]);
  let startTime = Date.now();
  let realTimeInfo = $state({
    elapsed: undefined,
    remaining: undefined
  });

  // Extract real time information from progress message
  $effect(() => {
    if (!progress?.message) return;
    console.log('🔍 Processing message:', progress.message);

    // Multiple patterns to match different Whisper progress formats
    const patterns = [
      // Pattern 1: Our custom format: "Progress: 50% (1000/2000) | Elapsed: 00:30 | Remaining: 01:30"
      /Progress:\s*(\d+)%.*Elapsed:\s*([^|]+)\s*\|\s*Remaining:\s*([^|]+)/i,
      
      // Pattern 2: Standard tqdm format: "Progress: 50% (1000/2000) | Elapsed: 00:30 | ETA: 00:30"
      /Progress:\s*(\d+)%.*Elapsed:\s*([^|]+)\s*\|\s*ETA:\s*([^|]+)/i,
      
      // Pattern 3: CLI output with tqdm: "CLI: 1%|▏| 2996/222478 [00:05<07:18, 500.22frames/s]"
      /CLI:.*?(\d+)%[^[]*\[([^<]+)<([^,]+),/,
      
      // Pattern 4: Simple format with brackets: "1%|▏| 2996/222478 [00:05<07:18, 500.22frames/s]"
      /(\d+)%[^[]*\[([^<]+)<([^,]+),/,
      
      // Pattern 5: Frame progress: "Processing frame 1000/2000 (50%)"
      /Processing frame \d+\/\d+ \((\d+)%\)/,
    ];

    let matched = false;
    
    for (const pattern of patterns) {
      const match = progress.message.match(pattern);
      console.log('🎯 Testing pattern:', pattern, 'Match:', match);
      
      if (match) {
        matched = true;
        
        if (match.length >= 4) {
          // Has elapsed and remaining time
          const [, progressStr, elapsed, remaining] = match;
          console.log('⏱️ Extracted times:', { progressStr, elapsed, remaining });

          // Parse time strings like "00:06" or "07:18" to seconds
          const parseTimeToSeconds = (timeStr) => {
            if (!timeStr) return 0;
            const cleanTime = timeStr.trim();
            console.log('🔍 Parsing time string:', cleanTime);
            
            // Handle different time formats
            const parts = cleanTime.split(':').map(p => parseInt(p, 10));
            let seconds = 0;
            
            if (parts.length === 2) {
              // MM:SS format
              seconds = parts[0] * 60 + parts[1];
            } else if (parts.length === 3) {
              // HH:MM:SS format
              seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
            } else if (parts.length === 1) {
              // Just seconds
              seconds = parts[0];
            }
            
            console.log('🔍 Parsed seconds:', seconds, 'from', cleanTime);
            return seconds;
          };

          const elapsedSeconds = parseTimeToSeconds(elapsed);
          const remainingSeconds = parseTimeToSeconds(remaining);
          console.log('🕒 Final parsed times (seconds):', { 
            elapsed: elapsedSeconds, 
            remaining: remainingSeconds,
            originalElapsed: elapsed,
            originalRemaining: remaining
          });

          // Only update if we got valid different values
          if (elapsedSeconds !== remainingSeconds || (elapsedSeconds === 0 && remainingSeconds === 0)) {
            realTimeInfo = {
              elapsed: elapsedSeconds,
              remaining: remainingSeconds,
            };
          } else {
            console.log('⚠️ Elapsed and remaining are the same, might be parsing error');
          }
        }
        break;
      }
    }
    
    if (!matched) {
      console.log('🔍 No time pattern matched, checking for simple progress updates');
      // Look for any percentage in the message to show we're getting updates
      const simpleMatch = progress.message.match(/(\d+)%/);
      if (simpleMatch) {
        console.log('📊 Found simple progress:', simpleMatch[1] + '%');
      }
    }
  });

  // Safe log management with manual tracking
  let lastProcessedMessage = '';
  let lastProcessedStage = '';

  // Function to add log entries without causing reactivity loops
  function addLogEntry(level, message, details) {
    const entry = {
      id: `${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
      level,
      message,
      details,
    };

    // Use snapshot to avoid reactivity in effect
    const currentEntries = $state.snapshot(logEntries);
    logEntries = [...currentEntries, entry];
  }

  // Only track progress changes, not logEntries changes
  $effect(() => {
    if (!progress) return;

    // Add CLI message - allow CLI outputs to show even if repeated
    if (progress.message) {
      if (progress.message.startsWith('CLI:') || progress.message !== lastProcessedMessage) {
        lastProcessedMessage = progress.message;
        addLogEntry('info', progress.message);
      }
    }

    // Add stage change messages only if stage changed
    if (progress.stage && progress.stage !== lastProcessedStage) {
      lastProcessedStage = progress.stage;

      // Get snapshot for checking existing entries
      const currentEntries = $state.snapshot(logEntries);

      switch (progress.stage) {
        case 'initializing':
          if (currentEntries.length === 0) {
            addLogEntry('info', `Starting processing pipeline for: ${currentFile}`);
          }
          break;
        case 'loading_model':
          if (!currentEntries.some(e => e.message.includes('Loading Whisper'))) {
            addLogEntry('info', 'Loading Whisper AI model...');
          }
          break;
        case 'transcribing':
          if (!currentEntries.some(e => e.message.includes('Starting transcription'))) {
            addLogEntry('info', 'Starting transcription process');
          }
          break;
      }
    }
  });

  const progressPercent = $derived(progress?.progress || 0);
  const currentStage = $derived(progress?.stage || 'initializing');
</script>

<div class="flex-1 flex flex-col p-8">
  <div class="w-full max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <div class="text-center">
      <div class="flex items-center justify-center gap-3 mb-2">
        <div class="relative">
          <Icon name="file-audio" size={32} class="text-primary-500" />
          {#if !isPaused}
            <Icon name="loader2" size={16} class="text-primary-500 absolute -top-1 -right-1" />
          {/if}
        </div>
        <div>
          <h2 class="text-2xl font-semibold text-gray-800 dark:text-gray-200">
            Processing Audio File
          </h2>
          <p class="text-gray-600 dark:text-gray-400 text-sm">
            {currentFile}
          </p>
        </div>
      </div>

      {#if isPaused}
        <div class="inline-flex items-center gap-2 bg-warning-50 dark:bg-warning-900 dark:bg-opacity-20 text-warning-800 dark:text-warning-200 px-3 py-1 rounded-full text-sm">
          <Icon name="pause" size={16} />
          Processing Paused
        </div>
      {/if}
    </div>

    <!-- Main Progress Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Column - Stage Indicator -->
      <div class="space-y-6">
        <StageIndicator
          currentStage={currentStage}
          progress={progressPercent}
        />

        <!-- Overall Progress -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
            Overall Progress
          </h3>

          <ProgressBar
            value={progressPercent}
            size="lg"
            color="primary"
            showLabel={true}
            label="{Math.round(progressPercent)}% Complete"
            class="mb-4"
          />

          <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
            <span>Stage: {currentStage.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
            <span>{Math.round(progressPercent)}%</span>
          </div>
        </div>
      </div>

      <!-- Right Column - Time Estimation -->
      <div class="space-y-6">
        <TimeEstimation
          {startTime}
          currentProgress={progressPercent}
          realElapsed={realTimeInfo.elapsed}
          realRemaining={realTimeInfo.remaining}
        />

        <!-- Processing Controls -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
            Processing Controls
          </h3>

          <div class="flex gap-3">
            {#if onPause && onResume}
              <Button
                variant={isPaused ? "primary" : "secondary"}
                onclick={isPaused ? onResume : onPause}
              >
                {#if isPaused}
                  <Icon name="play" size={16} class="mr-2" />
                  Resume
                {:else}
                  <Icon name="pause" size={16} class="mr-2" />
                  Pause
                {/if}
              </Button>
            {/if}

            <Button
              variant="error"
              onclick={onCancel}
            >
              <Icon name="x" size={16} class="mr-2" />
              Cancel Processing
            </Button>
          </div>

          <div class="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <p class="text-xs text-gray-600 dark:text-gray-400">
              💡 You can pause processing at any time and resume later.
              Progress will be saved automatically.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Processing Log - Hidden for cleaner UI -->
    <!-- <ProcessingLog
      entries={logEntries}
      isProcessing={!isPaused}
      maxHeight="h-96"
    /> -->
  </div>
</div>

<style>
  .shadow-soft {
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  }

</style>