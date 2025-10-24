import {
  CodeCell,
  CodeCellModel,
  ICellModel,
  ICodeCellModel
} from '@jupyterlab/cells';
import { IChangedArgs } from '@jupyterlab/coreutils';
import { Notebook, NotebookPanel, NotebookActions } from '@jupyterlab/notebook';
import { CellChange, createMutex, ISharedCodeCell } from '@jupyter/ydoc';
import { IOutputAreaModel, OutputAreaModel } from '@jupyterlab/outputarea';
import { requestAPI } from '../handler';
import { ResettableNotebook } from './notebook';

const globalModelDBMutex = createMutex();

/**
 * The class name added to the cell when dirty.
 */
const DIRTY_CLASS = 'jp-mod-dirty';

(CodeCellModel.prototype as any)._onSharedModelChanged = function (
  slot: ISharedCodeCell,
  change: CellChange
) {
  if (change.streamOutputChange) {
    globalModelDBMutex(() => {
      for (const streamOutputChange of change.streamOutputChange!) {
        if ('delete' in streamOutputChange) {
          this._outputs.removeStreamOutput(streamOutputChange.delete!);
        }
        if ('insert' in streamOutputChange) {
          this._outputs.appendStreamOutput(
            streamOutputChange.insert!.toString()
          );
        }
      }
    });
  }

  if (change.outputsChange) {
    globalModelDBMutex(() => {
      let retain = 0;
      for (const outputsChange of change.outputsChange!) {
        if ('retain' in outputsChange) {
          retain += outputsChange.retain!;
        }
        if ('delete' in outputsChange) {
          for (let i = 0; i < outputsChange.delete!; i++) {
            this._outputs.remove(retain);
          }
        }
        if ('insert' in outputsChange) {
          // Inserting an output always results in appending it.
          for (const output of outputsChange.insert!) {
            // For compatibility with older ydoc where a plain object,
            // (rather than a Map instance) could be provided.
            // In a future major release the use of Map will be required.
            if ('toJSON' in output) {
              const json = (output as { toJSON: () => any }).toJSON();
              if (json.metadata?.url) {
                // fetch the output from ouputs service
                requestAPI(json.metadata.url).then(data => {
                  this._outputs.add(data);
                });
              } else {
                this._outputs.add(json);
              }
            } else {
              this._outputs.add(output);
            }
          }
        }
      }
    });
  }
  if (change.executionCountChange) {
    if (
      change.executionCountChange.newValue &&
      (this.isDirty || !change.executionCountChange.oldValue)
    ) {
      this._setDirty(false);
    }
    this.stateChanged.emit({
      name: 'executionCount',
      oldValue: change.executionCountChange.oldValue,
      newValue: change.executionCountChange.newValue
    });
  }

  if (change.sourceChange && this.executionCount !== null) {
    this._setDirty(this._executedCode !== this.sharedModel.getSource().trim());
  }
};

(CodeCellModel as any).prototype.onOutputsChange = function (
  sender: IOutputAreaModel,
  event: IOutputAreaModel.ChangedArgs
) {
  // no-op
};

/* An OutputAreaModel that loads outputs from outputs service */
class RtcOutputAreaModel extends OutputAreaModel implements IOutputAreaModel {
  constructor(options: IOutputAreaModel.IOptions = {}) {
    super({ ...options, values: [] }); // Don't pass values to OutputAreaModel
    if (options.values?.length) {
      const firstValue = options.values[0];
      if ((firstValue as any).metadata?.url) {
        let outputsUrl = (firstValue as any).metadata.url;
        // Skip the last section with *.output
        outputsUrl = outputsUrl.substring(0, outputsUrl.lastIndexOf('/'));
        requestAPI(outputsUrl)
          .then(outputs => {
            (outputs as any).forEach((output: any) => {
              if (!(this as any).isDisposed) {
                const index = (this as any)._add(output) - 1;
                const item = (this as any).list.get(index);
                item.changed.connect((this as any)._onGenericChange, this);
              }
            });
          })
          .catch(error => {
            console.error('Error fetching output:', error);
          });
      } else {
        options.values.forEach((output: any) => {
          if (!(this as any).isDisposed) {
            const index = (this as any)._add(output) - 1;
            const item = (this as any).list.get(index);
            item.changed.connect((this as any)._onGenericChange, this);
          }
        });
      }
    }
  }
}

/**
 * NOTE: We should upstream this fix. This is a bug in JupyterLab.
 *
 * The execution count comes back from the kernel immediately
 * when the execute request is made by the client, even thought
 * cell might still be running. JupyterLab holds this value in
 * memory with a Promise to set it later, once the execution
 * state goes back to Idle.
 *
 * In CRDT world, we don't need to do this gymnastics, holding
 * the state in a Promise. Instead, we can just watch the
 * executionState and executionCount in the CRDT being maintained
 * by the server-side model.
 *
 * This is a big win! It means user can close and re-open a
 * notebook while a list of executed cells are queued.
 */
(CodeCell.prototype as any).onStateChanged = function (
  model: ICellModel,
  args: IChangedArgs<any>
): void {
  switch (args.name) {
    case 'executionCount':
      this._updatePrompt();
      break;
    case 'isDirty':
      if ((model as ICodeCellModel).isDirty) {
        this.addClass(DIRTY_CLASS);
      } else {
        this.removeClass(DIRTY_CLASS);
      }
      break;
    default:
      break;
  }

  // Always update prompt to check for awareness state on any state change
  this._updatePrompt();
};

/**
 * Override the _updatePrompt method to check awareness execution state for real-time updates.
 * This method integrates with the server-side cell execution state tracking to provide
 * real-time visual feedback about cell execution status across collaborative sessions.
 *
 * Key behaviors:
 * - Shows '*' for cells that are busy/running
 * - Shows execution count for idle cells
 * - Handles never-executed cells gracefully without triggering reconnection
 * - Provides fallback behavior when awareness connection is lost
 */
(CodeCell.prototype as any)._updatePrompt = function (): void {
  let prompt: string;

  // Get cell execution state from awareness (real-time)
  const cellExecutionState = this._getCellExecutionStateFromAwareness();

  // Check execution state from awareness
  if (cellExecutionState === 'busy') {
    // Cell is queued or actively executing - show spinning indicator
    prompt = '*';
  } else {
    // Cell is idle, never executed, or connection lost - show execution count as fallback
    prompt = `${this.model.executionCount || ''}`;
  }

  this._setPrompt(prompt);
};

/**
 * Get execution state for this cell from awareness system.
 *
 * This method queries the collaborative awareness state to determine the current
 * execution status of a cell. It distinguishes between three scenarios:
 *
 * Returns:
 * - 'busy'|'idle'|'running': actual execution state from awareness
 * - null: awareness connection lost (should trigger reconnection)
 * - undefined: cell never executed (should not trigger reconnection)
 *
 * The distinction between null and undefined is crucial for preventing
 * unnecessary reconnection attempts when cells have simply never been executed.
 */
(CodeCell.prototype as any)._getCellExecutionStateFromAwareness = function ():
  | string
  | null
  | undefined {
  const notebook = this.parent?.parent;
  if (!notebook?.model?.sharedModel?.awareness) {
    return null; // Connection lost
  }

  const awareness = notebook.model.sharedModel.awareness;
  const awarenessStates = awareness.getStates();

  // Check if awareness has any states at all
  if (awarenessStates.size === 0) {
    return null; // Connection lost
  }

  // Look through all client states for cell execution states
  let hasAnyExecutionStates = false;
  for (const [_, clientState] of awarenessStates) {
    if (clientState && 'cell_execution_states' in clientState) {
      const cellStates = clientState['cell_execution_states'];
      hasAnyExecutionStates = true;
      if (cellStates && this.model.sharedModel.getId() in cellStates) {
        return cellStates[this.model.sharedModel.getId()];
      }
    }
  }

  if (hasAnyExecutionStates) {
    // We have execution states from server, but this cell is not in them
    // This means the cell has never been executed
    return undefined; // Never executed
  } else {
    // No execution states at all - connection issue
    return null; // Connection lost
  }
};

/**
 * Initialize CodeCell state including awareness listener setup.
 *
 * This method is called once during cell creation to set up the awareness
 * listener that will track cell execution states in real-time across
 * collaborative sessions. It ensures that each cell has a properly
 * configured awareness listener without redundant setup calls.
 */
(CodeCell.prototype as any).initializeState = function (): CodeCell {
  // Set up awareness listener for prompt updates
  this._setupAwarenessListener();
  return this;
};

/**
 * Set up awareness listener for prompt updates.
 *
 * This method establishes a listener on the awareness system that will
 * automatically update the cell's prompt when execution states change.
 * It waits for the cell to be fully ready before attempting to access
 * awareness data, ensuring reliable setup.
 *
 * The listener is stored for proper cleanup during cell disposal.
 */
(CodeCell.prototype as any)._setupAwarenessListener = function (): void {
  const updatePromptFromAwareness = () => {
    this._updatePrompt();
  };

  // The CodeCell instantiation needs to be fully ready before
  // attempting to fetch its awareness data.
  this.ready.then(() => {
    const notebook = this.parent?.parent;
    if (notebook?.model?.sharedModel?.awareness) {
      notebook.model.sharedModel.awareness.on(
        'change',
        updatePromptFromAwareness
      );

      // Store the listener for cleanup
      this._awarenessUpdateListener = updatePromptFromAwareness;
      this._awarenessInstance = notebook.model.sharedModel.awareness;

      // Perform initial prompt update
      this._updatePrompt();
    }
  });
};

/**
 * Override dispose to clean up awareness listener.
 *
 * This ensures that when a cell is disposed, its awareness listener
 * is properly removed to prevent memory leaks and unexpected behavior.
 */
const originalDispose = CodeCell.prototype.dispose;
(CodeCell.prototype as any).dispose = function (): void {
  if (this._awarenessUpdateListener && this._awarenessInstance) {
    this._awarenessInstance.off('change', this._awarenessUpdateListener);
    this._awarenessUpdateListener = null;
    this._awarenessInstance = null;
  }
  originalDispose.call(this);
};

CodeCellModel.ContentFactory.prototype.createOutputArea = function (
  options: IOutputAreaModel.IOptions
): IOutputAreaModel {
  return new RtcOutputAreaModel(options);
};

export class RtcNotebookContentFactory
  extends NotebookPanel.ContentFactory
  implements NotebookPanel.IContentFactory
{
  createCodeCell(options: CodeCell.IOptions): CodeCell {
    return new CodeCell(options).initializeState();
  }

  createNotebook(options: Notebook.IOptions): Notebook {
    return new ResettableNotebook(options);
  }
}

// Add a handler for the outputCleared signal
NotebookActions.outputCleared.connect((sender, args) => {
  const { notebook, cell } = args;
  const cellId = cell.model.sharedModel.getId();
  const awareness = notebook.model?.sharedModel.awareness;
  const awarenessStates = awareness?.getStates();

  // FIRST: Clear outputs in YDoc for immediate real-time sync to all clients
  try {
    const sharedCodeCell = cell.model.sharedModel as ISharedCodeCell;
    sharedCodeCell.setOutputs([]);
    console.debug(`Cleared outputs in YDoc for cell ${cellId}`);
  } catch (error: unknown) {
    console.error('Error clearing YDoc outputs:', error);
  }

  if (awarenessStates?.size === 0) {
    console.log('Could not delete cell output, awareness is not present');
    return; // Early return since we can't get fileId without awareness
  }

  let fileId = null;
  for (const [_, state] of awarenessStates || []) {
    if (state && 'file_id' in state) {
      fileId = state['file_id'];
    }
  }

  if (fileId === null) {
    console.error('No fileId found in awareness');
    return; // Early return since we can't make API call without fileId
  }

  // SECOND: Send API request to clear outputs from disk storage
  try {
    requestAPI(`/api/outputs/${fileId}/${cellId}`, {
      method: 'DELETE'
    })
      .then(() => {
        console.debug(
          `Successfully cleared outputs from disk for cell ${cellId}`
        );
      })
      .catch((error: Error) => {
        console.error(
          `Failed to clear outputs from disk for cell ${cellId}:`,
          error
        );
      });
  } catch (error: unknown) {
    console.error('Error in disk output clearing process:', error);
  }
});
