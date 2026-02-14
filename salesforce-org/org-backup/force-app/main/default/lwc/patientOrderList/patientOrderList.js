import { LightningElement, wire } from 'lwc';
import getMyOrders from '@salesforce/apex/AzothPatientController.getMyOrders';

const COLUMNS = [
    { label: 'Order Number', fieldName: 'OrderNumber', type: 'text' },
    { label: 'Date', fieldName: 'EffectiveDate', type: 'date' },
    { label: 'Status', fieldName: 'Status', type: 'text' },
    { label: 'Amount', fieldName: 'TotalAmount', type: 'currency' }
];

export default class PatientOrderList extends LightningElement {
    columns = COLUMNS;
    orders = [];

    @wire(getMyOrders)
    wiredOrders({ error, data }) {
        if (data) {
            this.orders = data;
        } else if (error) {
            console.error(error);
        }
    }
}