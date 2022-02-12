db.trade.aggregate(
{
    $group: {
        _id: '',
        profit: { $sum: '$record.total_profit' },
        win: { $sum: '$record.win' },
        loss: { $sum: '$record.loss' },
        zero: { $sum: '$record.zero' },
    }
}, 
{
    $project: {
        _id: 0,
        profit: '$profit',
        win : '$win',
        loss : '$loss',
        zero : '$zero',
        total : { '$add' : [ '$loss', '$win' ] }
    }
},
{
    $project: {
        profit: 1,
        win : 1,
        loss : 1,
        zero : 1,
        win_rate : { $divide: [ "$win", "$total" ] }
    }
}

)