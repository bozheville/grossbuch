
var controller = function($scope, $http, $cookieStore, $timeout){
    $scope.title = 'Banka';
    $scope.initdate = '27.02.2014';
    $scope.showPopup = {TRFilters: false, TRUsers: false, Users: false, UserStat: false};
    $scope.base_url = '/';
    $scope.syncenabled = $cookieStore.get('syncenabled');
    $scope.exchData = {
        from: 0,
        to: 0,
        user: '',
        type: 'uah2usd'
    };

    $scope.transactionfilters = {
        filters:{
            debit:true,
            payout:true,
            credit:true,
            repayment:true,
            BuyUSD:true,
            SellUSD:true
        },
        users:{}
    };

    var initNew = function(e){
        $scope.pageinfo = e;
        $scope.saveduser = $cookieStore.get('user');
        for(user in $scope.pageinfo.users){
            var uid = $scope.pageinfo.users[user]._id;
            $scope.transactionfilters.users[uid] = true;
        }
        $scope.newTransaction = {
            type : 'debit',
            name : $scope.saveduser,
            amount: 20
        };
    };

    var initPage = function(){
        $http.get($scope.base_url + 'api/getinfo').success(function(e){
            initNew(e);
        });
    };

    $scope.processTransaction = function(){
        var errors = [];
        if(['debit', 'credit','repayment', 'payout', 'BuyUSD', 'SellUDS'].indexOf($scope.newTransaction.type) == -1){errors.push('type');}
        if(!$scope.newTransaction.name){errors.push('name');}
        if(!String($scope.newTransaction.amount).match(/^\d+$/)){errors.push('amount');}
        if(errors.length == 0){
            $http.get($scope.base_url + 'api/newTransaction/'+$scope.newTransaction.name+'/'+$scope.newTransaction.type+'/'+$scope.newTransaction.amount).success(function(e){
                $cookieStore.put('user', $scope.newTransaction.name);
                initNew(e);
            });
        } else {
            alert('Error in keys: ' + errors.join(', '));
        }
    };

    $scope.setTransaction = function(uid, type, amount){
        if(uid){
            $scope.newTransaction.name = uid;
            $scope.newTransaction.type = type;
            $scope.newTransaction.amount = amount;
        }
    };

    $scope.toggleSync = function(){
        $scope.syncenabled = !$scope.syncenabled;
        $cookieStore.put('syncenabled', $scope.syncenabled);
    };

    $scope.cancelTransaction = function(){
        if(confirm('Are you sure you want to cancel last transaction? You can\'t restore it.')){
            $http.get($scope.base_url + 'api/cancelTransaction/').success(function(e){
                initNew(e);
            });
        }
    };

    $scope.setAmount = function(sum){
        $scope.newTransaction.amount=sum;
    };

    $scope.togglePopup = function(type){
        $scope.showPopup[type] = !$scope.showPopup[type];
    };

    $scope.checkAll = function(type, checked){
        if(type == 'TRFilters'){
            for(var i in $scope.transactionfilters.filters){
                $scope.transactionfilters.filters[i] = checked;
            }
        } else if(type == 'TRUsers'){
            for(var i in $scope.transactionfilters.users){
                $scope.transactionfilters.users[i] = checked;
            }
        }

    };

    $scope.toggleUser = function(_id, value){
        value = value ? 1:0;
        $http.get($scope.base_url + 'api/toggleUser/'+_id+'/'+value);
    };

    $scope.exchange = function(){
        $http.get($scope.base_url + 'api/exchange/'+$scope.exchData.user+'/'+$scope.exchData.from+'/'+$scope.exchData.type+'/'+$scope.exchData.to).success(function(e){
            initNew(e);
        });
    };

    var updatePage = function(){
        if($scope.syncenabled){
            $scope.refresh();
        }
        $timeout(updatePage, 5000);
    };

    $scope.refresh = function(){
      $http.get($scope.base_url + 'api/getinfo').success(function(e){
            $scope.pageinfo.summary = e.summary;
            $scope.pageinfo.transactions = e.transactions;
            var changekeys = ['cedit', 'debit', 'disabled'];
            for(var i in e.users){
                for(var j in $scope.pageinfo.users){
                    if(e.users[i]._id == $scope.pageinfo.users[j]._id){
                        for(var k in changekeys){
                            $scope.pageinfo.users[j][changekeys[k]] = e.users[i][changekeys[k]];
                        }
                    }
                }
            }
        });
    };

    $scope.showstat = function(user){
        $http.get($scope.base_url+'api/getDebitStat/'+user).success(function(e){
            if(e.ok == 1){
                $scope.pageinfo.UserStat = e.result;
                $scope.showPopup['UserStat'] = true;
                var data = [];
                data.push(['month', 'debit']);
                for(var i in e.result){
                    data.push([e.result[i]._id, e.result[i].debit]);
                }
                drawChart('userstatchart', data);
                $scope.ShowUserstatName = '';
                for(var i in $scope.pageinfo.users){
                    if($scope.pageinfo.users[i]._id == user){
                        $scope.ShowUserstatName = $scope.pageinfo.users[i].name;
                        break;
                    }
                }
            }
        });
    };

    $scope.toggleTransactionUser = function(user){
        var checked = 0;
        for(var i in $scope.transactionfilters.users){
            if($scope.transactionfilters.users[i]){
                checked++;
            }
        }
        if(checked == 1){
            for(var i in $scope.transactionfilters.users){
                $scope.transactionfilters.users[i] = true;
            }
        } else{
            for(var i in $scope.transactionfilters.users){
                if(i == user){
                    $scope.transactionfilters.users[i] = true;
                } else{
                    $scope.transactionfilters.users[i] = false;
                }

            }
        }
    };

    $scope.toggleTransactionType = function(type){
        var checked = 0;
        for(var i in $scope.transactionfilters.filters){
            if($scope.transactionfilters.filters[i]){
                checked++;
            }
        }
        if(checked == 1){
            for(var i in $scope.transactionfilters.filters){
                $scope.transactionfilters.filters[i] = true;
            }
        } else{
            for(var i in $scope.transactionfilters.filters){
                if(i == type){
                    $scope.transactionfilters.filters[i] = true;
                } else{
                    $scope.transactionfilters.filters[i] = false;
                }

            }
        }
    };

    initPage();
    $timeout(updatePage, 5000);

};

angular.module('grossbuch', ['ngCookies']);