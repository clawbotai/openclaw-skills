import { LightningElement, api } from 'lwc';

export default class DatatableBase extends LightningElement {
    @api tableData = [];
    @api columns = [];
    @api keyField = 'id';
    @api hideCheckboxColumn = false;

    handleRowAction(event) {
        // Bubble up the event
        const actionName = event.detail.action.name;
        const row = event.detail.row;
        this.dispatchEvent(new CustomEvent('rowaction', {
            detail: { action: { name: actionName }, row: row }
        }));
    }
}