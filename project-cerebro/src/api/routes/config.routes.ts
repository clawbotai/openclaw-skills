/**
 * Config routes - expose configuration to frontend
 */

import { FastifyInstance } from 'fastify';
import { getConfig } from '../../lib/config';

export function registerConfigRoutes(server: FastifyInstance): void {
  /**
   * GET /api/config/models
   * Get available models from OpenClaw config
   */
  server.get('/api/config/models', async () => {
    const config = getConfig();
    
    // Read models from OpenClaw config file
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    
    const openclawConfigPath = path.join(os.homedir(), '.openclaw', 'openclaw.json');
    let models: Array<{ alias: string; id: string; provider: string }> = [];
    
    try {
      const openclawConfig = JSON.parse(fs.readFileSync(openclawConfigPath, 'utf-8'));
      const modelEntries = openclawConfig?.agents?.defaults?.models || {};
      
      models = Object.entries(modelEntries)
        .filter(([id]) => id !== 'openrouter/auto') // Skip the auto entry
        .map(([id, info]: [string, any]) => {
          // Extract provider from id (e.g., "openrouter/google/gemini-3-flash-preview")
          const parts = id.split('/');
          const provider = parts.length >= 2 ? parts[0] : 'unknown';
          
          return {
            id,
            alias: info?.alias || id.replace(/\//g, '-'),
            provider: provider === 'openrouter' && parts.length >= 2 ? parts[1] : provider,
          };
        });
      
      // Add the auto model at the top if it exists
      if (modelEntries['openrouter/auto']) {
        models.unshift({
          id: 'openrouter/auto',
          alias: 'auto',
          provider: 'openrouter',
        });
      }
    } catch (error) {
      console.error('Failed to read OpenClaw config:', error);
      // Fallback models
      models = [
        { alias: 'auto', id: 'openrouter/openrouter/auto', provider: 'openrouter' },
        { alias: 'gemini-flash', id: 'openrouter/google/gemini-3-flash-preview', provider: 'google' },
        { alias: 'gemini-pro', id: 'openrouter/google/gemini-3-pro-preview', provider: 'google' },
        { alias: 'claude-sonnet', id: 'openrouter/anthropic/claude-sonnet-4.5', provider: 'anthropic' },
        { alias: 'claude-opus', id: 'openrouter/anthropic/claude-opus-4.5', provider: 'anthropic' },
      ];
    }
    
    return { models };
  });
}
