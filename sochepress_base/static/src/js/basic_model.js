odoo.define('sochepress_base.basic_model', function (require) {
    'use strict';

    var BasicModel = require("web.BasicModel");

    BasicModel.include({
        /**
         * Fetches all the values associated to the given fieldName.
         *
         * @param {Object} record - an element from the localData
         * @param {Object} fieldName - the name of the field
         * @param {Object} fieldInfo
         * @returns {Promise<any>}
         *          The promise is resolved with the fetched special values.
         *          If this data is the same as the previously fetched one
         *          (for the given parameters), no RPC is done and the promise
         *          is resolved with the undefined value.
         */
    _applyOnChange: function (values, record, viewType) {
        var self = this;
        var defs = [];
        var rec;
        viewType = viewType || record.viewType;
        record._changes = record._changes || {};
        _.each(values, function (val, name) {
            var field = record.fields[name];
            if (!field) {
                // this field is unknown so we can't process it for now (it is not
                // in the current view anyway, otherwise it wouldn't be unknown.
                // we store its value without processing it, so that if we later
                // on switch to another view in which this field is displayed,
                // we could process it as we would know its type then.
                // use case: an onchange sends a create command for a one2many,
                // in the dict of values, there is a value for a field that is
                // not in the one2many list, but that is in the one2many form.
                record._rawChanges[name] = val;
                return;
            }
            if (record._rawChanges[name]) {
                // if previous _rawChanges exists, clear them since the field is now knwon
                // and restoring outdated onchange over posterious change is wrong
                delete record._rawChanges[name];
            }
            var oldValue = name in record._changes ? record._changes[name] : record.data[name];
            var id;
            if (field.type === 'many2one') {
                id = false;
                // in some case, the value returned by the onchange can
                // be false (no value), so we need to avoid creating a
                // local record for that.
                if (val) {
                    // when the value isn't false, it can be either
                    // an array [id, display_name] or just an id.
                    var data = _.isArray(val) ?
                        {id: val[0], display_name: val[1]} :
                        {id: val};
                    if (!oldValue || (self.localData[oldValue].res_id !== data.id)) {
                        // only register a change if the value has changed
                        rec = self._makeDataPoint({
                            context: record.context,
                            data: data,
                            modelName: field.relation,
                            parentID: record.id,
                        });
                        id = rec.id;
                        record._changes[name] = id;
                    }
                } else {
                    record._changes[name] = false;
                }
            } else if (field.type === 'reference') {
                id = false;
                if (val) {
                    var ref = val.split(',');
                    var modelName = ref[0];
                    var resID = parseInt(ref[1]);
                    if (!oldValue || self.localData[oldValue].res_id !== resID ||
                        self.localData[oldValue].model !== modelName) {
                        // only register a change if the value has changed
                        rec = self._makeDataPoint({
                            context: record.context,
                            data: {id: parseInt(ref[1])},
                            modelName: modelName,
                            parentID: record.id,
                        });
                        defs.push(self._fetchNameGet(rec));
                        id = rec.id;
                        record._changes[name] = id;
                    }
                } else {
                    record._changes[name] = id;
                }
            } else if (field.type === 'one2many' || field.type === 'many2many') {
                var listId = record._changes[name] || record.data[name];
                var list;
                if (listId) {
                    list = self.localData[listId];
                } else {
                    var fieldInfo = record.fieldsInfo[viewType][name];
                    if (!fieldInfo) {
                        return; // ignore changes of x2many not in view
                    }
                    var view = fieldInfo.views && fieldInfo.views[fieldInfo.mode];
                    list = self._makeDataPoint({
                        fields: view ? view.fields : fieldInfo.relatedFields,
                        fieldsInfo: view ? view.fieldsInfo : fieldInfo.fieldsInfo,
                        limit: fieldInfo.limit,
                        modelName: field.relation,
                        parentID: record.id,
                        static: true,
                        type: 'list',
                        viewType: view ? view.type : fieldInfo.viewType,
                    });
                }
                // TODO: before registering the changes, verify that the x2many
                // value has changed
                record._changes[name] = list.id;
                list._changes = list._changes && Array.isArray(list._changes) ? list._changes : [];

                // save it in case of a [5] which will remove the _changes
                var oldChanges = list._changes;
                _.each(val, function (command) {
                    var rec, recID;
                    if (command[0] === 0 || command[0] === 1) {
                        // CREATE or UPDATE
                        if (command[0] === 0 && command[1]) {
                            // updating an existing (virtual) record
                            var previousChange = _.find(oldChanges, function (operation) {
                                var child = self.localData[operation.id];
                                return child && (child.ref === command[1]);
                            });
                            recID = previousChange && previousChange.id;
                            rec = self.localData[recID];
                        }
                        if (command[0] === 1 && command[1]) {
                            // updating an existing record
                            rec = self.localData[list._cache[command[1]]];
                        }
                        if (!rec) {
                            var params = {
                                context: list.context,
                                fields: list.fields,
                                fieldsInfo: list.fieldsInfo,
                                modelName: list.model,
                                parentID: list.id,
                                viewType: list.viewType,
                                ref: command[1],
                            };
                            if (command[0] === 1) {
                                params.res_id = command[1];
                            }
                            rec = self._makeDataPoint(params);
                            list._cache[rec.res_id] = rec.id;
                        }
                        // Do not abandon the record if it has been created
                        // from `default_get`. The list has a savepoint only
                        // after having fully executed `default_get`.
                        rec._noAbandon = !list._savePoint;
                        list._changes.push({operation: 'ADD', id: rec.id});
                        if (command[0] === 1) {
                            list._changes.push({operation: 'UPDATE', id: rec.id});
                        }
                        defs.push(self._applyOnChange(command[2], rec));
                    } else if (command[0] === 4) {
                        // LINK TO
                        linkRecord(list, command[1]);
                    } else if (command[0] === 5) {
                        // DELETE ALL
                        list._changes = [{operation: 'REMOVE_ALL'}];
                    } else if (command[0] === 6) {
                        list._changes = [{operation: 'REMOVE_ALL'}];
                        _.each(command[2], function (resID) {
                            linkRecord(list, resID);
                        });
                    }
                });
                var def = self._readUngroupedList(list).then(function () {
                    var x2ManysDef = self._fetchX2ManysBatched(list);
                    var referencesDef = self._fetchReferencesBatched(list);
                    return Promise.all([x2ManysDef, referencesDef]);
                });
                defs.push(def);
            } else {
                var newValue = self._parseServerValue(field, val);
                if (newValue !== oldValue) {
                    record._changes[name] = newValue;
                }
            }
        });
        return Promise.all(defs);

        // inner function that adds a record (based on its res_id) to a list
        // dataPoint (used for onchanges that return commands 4 (LINK TO) or
        // commands 6 (REPLACE WITH))
        function linkRecord (list, resID) {
            rec = self.localData[list._cache[resID]];
            if (rec) {
                // modifications done on a record are discarded if the onchange
                // uses a LINK TO or a REPLACE WITH
                self.discardChanges(rec.id);
            }
            // the dataPoint id will be set when the record will be fetched (for
            // now, this dataPoint may not exist yet)
            list._changes.push({
                operation: 'ADD',
                id: rec ? rec.id : null,
                resID: resID,
            });
        }
    },
    _applyX2ManyChange: function (record, fieldName, command, options) {
        if (command.operation === 'TRIGGER_ONCHANGE') {
            // the purpose of this operation is to trigger an onchange RPC, so
            // there is no need to apply any change on the record (the changes
            // have probably been already applied and saved, usecase: many2many
            // edition in a dialog)
            return Promise.resolve();
        }

        var self = this;
        var localID = (record._changes && record._changes[fieldName]) || record.data[fieldName];
        var list = this.localData[localID];
        var field = record.fields[fieldName];
        var viewType = (options && options.viewType) || record.viewType;
        var fieldInfo = record.fieldsInfo[viewType][fieldName];
        var view = fieldInfo.views && fieldInfo.views[fieldInfo.mode];
        var def, rec;
        var defs = [];
        list._changes = list._changes && Array.isArray(list._changes) ? list._changes : [];

        switch (command.operation) {
            case 'ADD':
                // for now, we are in the context of a one2many field
                // the command should look like this:
                // { operation: 'ADD', id: localID }
                // The corresponding record may contain value for fields that
                // are unknown in the list (e.g. fields that are in the
                // subrecord form view but not in the kanban or list view), so
                // to ensure that onchanges are correctly handled, we extend the
                // list's fields with those in the created record
                var newRecord = this.localData[command.id];
                _.defaults(list.fields, newRecord.fields);
                _.defaults(list.fieldsInfo, newRecord.fieldsInfo);
                newRecord.fields = list.fields;
                newRecord.fieldsInfo = list.fieldsInfo;
                newRecord.viewType = list.viewType;
                list._cache[newRecord.res_id] = newRecord.id;
                list._changes.push(command);
                break;
            case 'ADD_M2M':
                // force to use link command instead of create command
                list._forceM2MLink = true;
                // handle multiple add: command[2] may be a dict of values (1
                // record added) or an array of dict of values
                var data = _.isArray(command.ids) ? command.ids : [command.ids];

                // Ensure the local data repository (list) boundaries can handle incoming records (data)
                if (data.length + list.res_ids.length > list.limit) {
                    list.limit = data.length + list.res_ids.length;
                }

                var list_records = {};
                _.each(data, function (d) {
                    rec = self._makeDataPoint({
                        context: record.context,
                        modelName: field.relation,
                        fields: view ? view.fields : fieldInfo.relatedFields,
                        fieldsInfo: view ? view.fieldsInfo : fieldInfo.fieldsInfo,
                        res_id: d.id,
                        data: d,
                        viewType: view ? view.type : fieldInfo.viewType,
                        parentID: list.id,
                    });
                    list_records[d.id] = rec;
                    list._cache[rec.res_id] = rec.id;
                    list._changes.push({operation: 'ADD', id: rec.id});
                });
                // read list's records as we only have their ids and optionally their display_name
                // (we can't use function readUngroupedList because those records are only in the
                // _changes so this is a very specific case)
                // this could be optimized by registering the fetched records in the list's _cache
                // so that if a record is removed and then re-added, it won't be fetched twice
                var fieldNames = list.getFieldNames();
                if (fieldNames.length) {
                    def = this._rpc({
                        model: list.model,
                        method: 'read',
                        args: [_.pluck(data, 'id'), fieldNames],
                        context: _.extend({}, record.context, field.context),
                    }).then(function (records) {
                        _.each(records, function (record) {
                            list_records[record.id].data = record;
                            self._parseServerData(fieldNames, list, record);
                        });
                        return Promise.all([
                            self._fetchX2ManysBatched(list),
                            self._fetchReferencesBatched(list)
                        ]);
                    });
                    defs.push(def);
                }
                break;
            case 'CREATE':
                var createOptions = _.extend({
                    context: command.context,
                    position: command.position
                }, options || {});

                def = this._addX2ManyDefaultRecord(list, createOptions).then(function (ids) {
                    _.each(ids, function(id){
                        if (command.position === 'bottom' && list.orderedResIDs && list.orderedResIDs.length >= list.limit) {
                            list.tempLimitIncrement = (list.tempLimitIncrement || 0) + 1;
                            list.limit += 1;
                        }
                        // FIXME: hack for lunch widget, which does useless default_get and onchange
                        if (command.data) {
                            return self._applyChange(id, command.data);
                        }
                    });
                });
                defs.push(def);
                break;
            case 'UPDATE':
                list._changes.push({operation: 'UPDATE', id: command.id});
                if (command.data) {
                    defs.push(this._applyChange(command.id, command.data));
                }
                break;
            case 'FORGET':
                // Unlink the record of list.
                list._forceM2MUnlink = true;
            case 'DELETE':
                // filter out existing operations involving the current
                // dataPoint, and add a 'DELETE' or 'FORGET' operation only if there is
                // no 'ADD' operation for that dataPoint, as it would mean
                // that the record wasn't in the relation yet
                var idsToRemove = command.ids;
                list._changes = _.reject(list._changes, function (change, index) {
                    var idInCommands = _.contains(command.ids, change.id);
                    if (idInCommands && change.operation === 'ADD') {
                        idsToRemove = _.without(idsToRemove, change.id);
                    }
                    return idInCommands;
                });
                _.each(idsToRemove, function (id) {
                    var operation = list._forceM2MUnlink ? 'FORGET': 'DELETE';
                    list._changes.push({operation: operation, id: id});
                });
                break;
            case 'DELETE_ALL':
                // first remove all pending 'ADD' operations
                list._changes = _.reject(list._changes, function (change) {
                    return change.operation === 'ADD';
                });

                // then apply 'DELETE' on existing records
                return this._applyX2ManyChange(record, fieldName, {
                    operation: 'DELETE',
                    ids: list.res_ids
                }, options);
            case 'REPLACE_WITH':
                // this is certainly not optimal... and not sure that it is
                // correct if some ids are added and some other are removed
                list._changes = [];
                var newIds = _.difference(command.ids, list.res_ids);
                var removedIds = _.difference(list.res_ids, command.ids);
                var addDef, removedDef, values;
                if (newIds.length) {
                    values = _.map(newIds, function (id) {
                        return {id: id};
                    });
                    addDef = this._applyX2ManyChange(record, fieldName, {
                        operation: 'ADD_M2M',
                        ids: values
                    }, options);
                }
                if (removedIds.length) {
                    var listData = _.map(list.data, function (localId) {
                        return self.localData[localId];
                    });
                    removedDef = this._applyX2ManyChange(record, fieldName, {
                        operation: 'DELETE',
                        ids: _.map(removedIds, function (resID) {
                            if (resID in list._cache) {
                                return list._cache[resID];
                            }
                            return _.findWhere(listData, {res_id: resID}).id;
                        }),
                    }, options);
                }
                return Promise.all([addDef, removedDef]);
            case 'MULTI':
                // allows batching multiple operations
                _.each(command.commands, function (innerCommand){
                    defs.push(self._applyX2ManyChange(
                        record,
                        fieldName,
                        innerCommand,
                        options
                    ));
                });
                break;
        }

        return Promise.all(defs).then(function () {
            // ensure to fetch up to 'limit' records (may be useful if records of
            // the current page have been removed)
            return self._readUngroupedList(list).then(function () {
                return self._fetchX2ManysBatched(list);
            });
        });
    },

    });

});
