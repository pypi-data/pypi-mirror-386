import { ToolService } from '../Services/ToolService';
import { AppStateService } from '../AppState';
import { DatabaseStateService, DatabaseType } from '../DatabaseStateService';

/**
 * Service responsible for fetching and processing notebook state information
 */
export class NotebookStateService {
  private toolService: ToolService;
  private currentNotebookId: string | null = null;

  constructor(toolService: ToolService) {
    this.toolService = toolService;
  }

  public updateNotebookId(newId: string): void {
    this.currentNotebookId = newId;
  }

  /**
   * Set the current notebook ID
   * @param notebookId ID of the notebook
   */
  public setNotebookId(notebookId: string | null): void {
    if (this.currentNotebookId !== notebookId) {
      console.log(
        `[NotebookStateService] Setting notebook ID to: ${notebookId}`
      );
      this.currentNotebookId = notebookId;

      // Also update the tool service's current notebook ID
      if (notebookId) {
        this.toolService.setCurrentNotebookId(notebookId);
      }
    }
  }

  /**
   * Get the current notebook ID
   * @returns The current notebook ID
   */
  public getNotebookId(): string | null {
    return this.currentNotebookId;
  }

  private cleanResult(result: any): any {
    const cleanedResult = [];
    if (result && result.content) {
      for (const content of result.content) {
        try {
          cleanedResult.push({
            ...content,
            text: JSON.parse(content.text)
          });
        } catch (e) {
          cleanedResult.push(content);
          console.error(e);
        }
      }
    }
    return cleanedResult;
  }

  /**
   * Fetches the current notebook state including summary, content, and edit history
   */
  public async fetchNotebookState(): Promise<string> {
    try {
      // Ensure the tool service is using the correct notebook context
      if (this.currentNotebookId) {
        this.toolService.setCurrentNotebookId(this.currentNotebookId);
      } else {
        console.log('No notebook ID set, using default context.');
      }

      // Pass the current notebook ID to ensure correct context
      console.log('Fetching notebook state for:', this.currentNotebookId);
      const notebook_summary =
        await this.toolService.notebookTools?.getNotebookSummary(
          this.currentNotebookId
        );

      console.log('Notebook Summary: ===', notebook_summary);

      const notebook_content = AppStateService.getNotebookTools().read_cells({
        // For backward compatibility, we'll still pass notebook_path
        // The tools will gradually be updated to use notebook_id
      });

      console.log('Notebook Content ===:', notebook_content);

      const cells: any[] = notebook_content?.cells || [];

      // Reverse the cells array
      const reversedCells = [...cells].reverse();

      // Take the first 3 cells from the reversed list (these are the most recent)
      const recentCells = reversedCells.slice(0, 3);

      // Format the recent cells for better readability
      let recentCellsStr =
        '\n\nMost Recent Cells From Most Recent To Oldest:\n';
      recentCells.forEach((cell, index) => {
        recentCellsStr += `\n--- ${index === 0 && 'Latest '}Cell ---\n${JSON.stringify(cell)}\n`;
      });

      // Use the local FilesystemTools instead of making HTTP request to MCP server
      let datasetsJson = '[]';
      try {
        if (this.toolService.filesystemTools) {
          const datasetsResult =
            await this.toolService.filesystemTools.list_datasets();
          datasetsJson = datasetsResult;
        } else {
          console.warn(
            'FilesystemTools not available, using empty dataset list'
          );
        }
      } catch (error) {
        console.error('Error fetching datasets via FilesystemTools:', error);
        datasetsJson = '[]';
      }

      console.log('Datasets:', datasetsJson);

      // Add the edit history
      let datasetStr = `\n\nAvailable Datasets:\n${datasetsJson}\n\n`;

      let summaryClean = '=== SUMMARY OF CELLS IN NOTEBOOK === \n\n';
      notebook_summary.forEach((cell: any) => {
        if (cell.id === 'planning_cell') {
          summaryClean += '- SAGE PLANNING CELL - \n';
          summaryClean += `cell_index: ${cell.index}, cell_id: ${cell.id}, summary: ${cell.summary}, cell_type: ${cell.cell_type}, next_step_string: ${cell.next_step_string}, current_step_string: ${cell.current_step_string}, empty: ${cell.empty}\n`;
          summaryClean += '- END SAGE PLANNING CELL -';
        } else {
          summaryClean += `cell_id: ${cell.id}, summary: ${cell.summary}, cell_index: ${cell.index}, cell_type: ${cell.cell_type}, empty: ${cell.empty}`;
        }

        summaryClean += '\n\n';
      });
      summaryClean += '=== END SUMMARY OF CELLS IN NOTEBOOK ===\n\n';
      console.log(summaryClean);
      let summaryToSend = summaryClean + datasetStr;

      const db_configs = DatabaseStateService.getState().configurations;
      if (db_configs.length !== 0) {
        let db_string = '=== DATABASE CONFIGURATIONS ===\n';
        DatabaseStateService.getState().configurations.forEach(db => {
          db_string += '\n- Name: ' + db.name + ', Type: ' + db.type + '\n';

          // Add Snowflake-specific configuration indicators
          if (db.type === DatabaseType.Snowflake && db.credentials) {
            const snowflakeConfig = db.credentials as any;
            db_string += `  WAREHOUSE_DEFINED=${snowflakeConfig.warehouse ? 'YES' : 'NO'}\n`;
            db_string += `  ROLE_DEFINED=${snowflakeConfig.role ? 'YES' : 'NO'}\n`;
            db_string += `  DATABASE_DEFINED=${snowflakeConfig.database ? 'YES' : 'NO'}\n`;
          }
        });
        db_string += '=== END DATABASE CONFIGURATIONS ===\n';

        db_string +=
          'Database Environment Variables\n' +
          '------------------------------\n' +
          '\n' +
          '{DB_NAME}_HOST\n' +
          '{DB_NAME}_PORT\n' +
          '{DB_NAME}_DATABASE\n' +
          '{DB_NAME}_USERNAME\n' +
          '{DB_NAME}_PASSWORD\n' +
          '{DB_NAME}_TYPE\n' +
          '{DB_NAME}_CONNECTION_URL      (optional)\n' +
          '{DB_NAME}_CONNECTION_JSON     (optional, JSON fallback)\n' +
          '\n' +
          'ADDITIONAL FOR SNOWFLAKE\n' +
          '------------------------\n' +
          '{DB_NAME}_ACCOUNT\n' +
          '{DB_NAME}_WAREHOUSE (optional)\n' +
          '{DB_NAME}_ROLE (optional)\n';

        db_string +=
          'Use these environment variables to connect to the databases. They are already set in the kernel';

        if (
          db_configs.filter(db => db.type === DatabaseType.Snowflake).length > 0
        ) {
          db_string +=
            '\n For connecting a snowflake database, use the ACCOUNT, USERNAME, and PASSWORD environment variables. Prioritize using snowflakes library to connect. If no warehouse is selected, use the first available warehouse in the account. If a database is defined, then connect to that one specifically. If the user requests a database on snowflake but it is different from the defined database, please suggest the user add a new database connection for it\n';
        }

        summaryToSend += db_string;
      }

      console.log('Summary Sent to LLM: ', summaryToSend);

      return summaryToSend;
    } catch (error) {
      console.error('Failed to fetch notebook state:', error);
      return '';
    }
  }
}
