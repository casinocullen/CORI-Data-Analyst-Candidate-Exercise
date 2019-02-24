#The propose of this code is to check the data types and subset to only Vermont and New Hampshire data.

library(data.table)
library(bit64)


bbdata <- fread("./Data/fbd_us_with_satellite_dec2017_v1.csv")
bbdata_sub <- subset(bbdata, bbdata$StateAbbr=="VT"|bbdata$StateAbbr=="NH")

write.csv(bbdata_sub, "./Result/bbdata_vt_nh.csv", row.names = FALSE)
