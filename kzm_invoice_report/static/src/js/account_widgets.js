openerp.inov_ma_account = function (instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    
    instance.web.account = instance.web.account || {};
    instance.web.account.bankStatementReconciliation = instance.web.account.bankStatementReconciliation.extend({
        start: function() {
            console.log('-----------------------------');
            console.log(this.statement_ids);
            console.log('-----------------------------');
            console.log(this);
            this._super();
            var self = this;
            // Retreive statement infos and reconciliation data from the model
            var lines_filter = [['journal_entry_id', '=', false], ['account_id', '=', false]];
            var deferred_promises = [];
            
            // Working on specified statement(s)
            if (self.statement_ids && self.statement_ids.length > 0) {
                lines_filter.push(['statement_id', 'in', self.statement_ids]);

                // If only one statement, display its name as title and allow to modify it
                if (self.single_statement) {
                    console.log('-------------HELOO---------------');
                    deferred_promises.push(self.model_bank_statement
                        .query(["name"])
                        .filter([['id', '=', self.statement_ids[0]]])
                        .first()
                        .then(function(title){
                            self.title = title.name;
                        })
                    );
                }
                // Anyway, find out how many statement lines are reconciled (for the progressbar)
                deferred_promises.push(self.model_bank_statement
                    .call("number_of_lines_reconciled", [self.statement_ids])
                    .then(function(num) {
                        self.already_reconciled_lines = num;
                    console.log(num);
                    })
                );
            }
            
            // Get operation templates
            deferred_promises.push(new instance.web.Model("account.statement.operation.template")
                .query(['id','name','account_id','label','amount_type','amount','tax_id','analytic_account_id'])
                .all().then(function (data) {
                    _(data).each(function(preset){
                        self.presets[preset.id] = preset;
                    });
                })
            );
            //************** Only presets with the same type ***************
            if (this.statement_ids.length > 0){
                stat = this.statement_ids[0];
                var model = new instance.web.Model("account.statement.operation.template");
                model.call("get_presets", [stat]).then(function(result) {
                    self.presets = result;
                });
            }
            //***************************************************************


            // Get the function to format currencies
            deferred_promises.push(new instance.web.Model("res.currency")
                .call("get_format_currencies_js_function")
                .then(function(data) {
                    self.formatCurrency = new Function("amount, currency_id", data);
                })
            );
    
            // Get statement lines
            deferred_promises.push(self.model_bank_statement_line
                .query(['id'])
                .filter(lines_filter)
                .order_by('statement_id, id')
                .all().then(function (data) {
                    self.st_lines = _(data).map(function(o){ return o.id });
                })
            );
            console.log('----------------------------');
            // When queries are done, render template and reconciliation lines
            return $.when.apply($, deferred_promises).then(function(){
    
                // If there is no statement line to reconcile, stop here
                if (self.st_lines.length === 0) {
                    self.$el.prepend(QWeb.render("bank_statement_nothing_to_reconcile"));
                    return;
                }
    
                // Create a dict account id -> account code for display facilities
                new instance.web.Model("account.account")
                    .query(['id', 'code'])
                    .all().then(function(data) {
                        _.each(data, function(o) { self.map_account_id_code[o.id] = o.code });
                    });

                // Create a dict currency id -> rounding factor
                new instance.web.Model("res.currency")
                    .query(['id', 'rounding'])
                    .all().then(function(data) {
                        _.each(data, function(o) { self.map_currency_id_rounding[o.id] = o.rounding });
                    });

                new instance.web.Model("ir.model.data")
                    .call("xmlid_to_res_id", ["account.menu_bank_reconcile_bank_statements"])
                    .then(function(data) {
                        self.reconciliation_menu_id = data;
                        self.doReloadMenuReconciliation();
                    });

                // Bind keyboard events TODO : méthode standard ?
                $("body").on("keypress", function (e) {
                    self.keyboardShortcutsHandler(e);
                });
    
                // Render and display
//                self.$el.prepend(QWeb.render("bank_statement_reconciliation", {
//                    title: self.title,
//                    single_statement: self.single_statement,
//                    total_lines: self.already_reconciled_lines+self.st_lines.length
//                }));
                console.log(self.title);
                self.updateProgressbar();
                var reconciliations_to_show = self.st_lines.slice(0,                            self.num_reconciliations_fetched_in_batch);
                console.log(reconciliations_to_show);
console.log(reconciliations_to_show.length);
                self.last_displayed_reconciliation_index = reconciliations_to_show.length;
                self.$(".reconciliation_lines_container").css("opacity", 0);
    
                // Display the reconciliations
//                return self.model_bank_statement_line
//                    .call("get_data_for_reconciliations", [reconciliations_to_show])
//                    .then(function (data) {
//                        var child_promises = [];
//                        while ((datum = data.shift()) !== undefined)
//                            child_promises.push(self.displayReconciliation(datum.st_line.id, 'inactive', false, true, datum.st_line, datum.reconciliation_proposition));
//                        $.when.apply($, child_promises).then(function(){
//                            self.$(".reconciliation_lines_container").animate({opacity: 1}, self.aestetic_animation_speed);
//                            self.getChildren()[0].set("mode", "match");
//                            self.updateShowMoreButton();
//                        });
//                    });
            });
        },

    });
}
