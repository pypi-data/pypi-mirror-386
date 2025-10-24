# Pipe Sidecar Component Example

This page demonstrates the PipeSidecar component displaying pipe configuration information.

## Add Note Pipe Example

<script setup>
const addNotePipeSidecar = {
  _version: '1.0.x',
  _class: 'open_ticket_ai.base.ticket_system_pipes.AddNotePipe',
  _extends: 'open_ticket_ai.core.pipes.ConfigurablePipe',
  _title: 'Add Note',
  _summary: 'Appends a note/article to a ticket in the connected system.',
  _category: 'ticket-system',
  _inputs: {
    placement: 'flat',
    alongside: ['id', 'use'],
    params: {
      ticket_system_id: 'Target ticket system ID from registry',
      ticket_id: 'Target ticket ID',
      note: 'Note body text or UnifiedNote object',
    },
  },
  _defaults: {
    'note.visibility': 'internal',
  },
  _output: {
    state_enum: ['ok', 'skipped', 'failed'],
    description: 'Pipe returns a state and optional payload.',
    payload_schema_ref: 'OpenTicketAI.Pipes.AddNote.Result',
    examples: {
      ok: {
        state: 'ok',
        payload: {
          note_id: 12345,
        },
      },
      skipped: {
        state: 'skipped',
        payload: {
          reason: 'empty_note',
        },
      },
      failed: {
        state: 'failed',
        error: 'ticket_not_found',
      },
    },
  },
  _errors: {
    fail: [
      {
        code: 'ticket_not_found',
        when: 'Ticket ID does not exist',
      },
      {
        code: 'backend_unauthorized',
        when: 'Adapter cannot authenticate',
      },
    ],
    break: [
      {
        code: 'config_invalid',
        when: 'Required config missing or invalid type',
      },
    ],
    continue: [
      {
        code: 'empty_note',
        when: 'Empty note body → pipe returns skipped',
      },
      {
        code: 'visibility_not_supported',
        when: 'Adapter ignores unsupported visibility → skipped',
      },
    ],
  },
  _engine_support: {
    on_failure: false,
    on_success: false,
  },
  _examples: {
    minimal: `- id: add_note
  use: open_ticket_ai.base.ticket_system_pipes.AddNotePipe
  ticket_system_id: "otobo_znuny"
  ticket_id: "{{ context.ticket.id }}"
  note: "Investigating"`,
    full: `- id: add_note_after_classification
  use: open_ticket_ai.base.ticket_system_pipes.AddNotePipe
  ticket_system_id: "otobo_znuny"
  ticket_id: "{{ context.last_created_ticket_id }}"
  note:
    body: |
      Root cause: database connection pool exhaustion
      Action: increase pool to 50; enable slow query log
    visibility: public`,
    large: `- id: add_note_conditional
  use: open_ticket_ai.base.ticket_system_pipes.AddNotePipe
  ticket_system_id: "otobo_znuny"
  ticket_id: "{{ context.ticket.id }}"
  note:
    body: >
      Auto-update: classified as {{ context.classification.queue }}
      priority={{ context.classification.priority }}
    visibility: internal`,
  },
}
</script>

<PipeSidecar :sidecar="addNotePipeSidecar" />

## With Action Buttons

<PipeSidecar :sidecar="addNotePipeSidecar">
  <template #actions>
    <div class="flex gap-2">
      <button class="px-4 py-2 bg-vp-brand text-white rounded hover:opacity-90 text-sm">
        Run Pipe
      </button>
      <button class="px-4 py-2 border border-vp-border text-vp-text-1 rounded hover:bg-vp-bg text-sm">
        View Docs
      </button>
    </div>
  </template>
</PipeSidecar>
