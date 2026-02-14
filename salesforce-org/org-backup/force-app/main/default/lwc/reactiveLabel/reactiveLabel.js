import { LightningElement, api } from 'lwc';

export default class ReactiveLabel extends LightningElement {
    @api label;
    @api value;
    @api unit;
}