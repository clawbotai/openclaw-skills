import { LightningElement, wire } from 'lwc';
import getMyOrders from '@salesforce/apex/AzothPatientController.getMyOrders';

const COLUMNS = [
    { label: 'Order #', fieldName: 'OrderNumber' },
    { label: 'Date', fieldName: 'EffectiveDate', type: 'date' },
    { label: 'Status', fieldName: 'Status' },
    { label: 'Amount', fieldName: 'TotalAmount', type: 'currency' }
];

export default class PatientDashboardClean extends LightningElement {
    columns = COLUMNS;

    @wire(getMyOrders)
    wiredOrders;
}