from box import Box 

ADDR_BEANSTALK = "0xC1E088fC1323b20BCBee9bd1B9fC9546db5624C5".lower()

# addresses of whitelisted silo tokens 
ADDR_BEAN = "0xBEA0000029AD1c77D3d5D23Ba2D8893dB9d1Efab".lower()
ADDR_BEAN_3CRV = "0xc9C32cd16Bf7eFB85Ff14e0c8603cc90F6F2eE49".lower()
ADDR_UR_BEAN = "0x1BEA0050E63e05FBb5D8BA2f10cf5800B6224449".lower()
ADDR_UR_BEAN_3CRV = "0x1BEA3CcD22F4EBd3d37d731BA31Eeca95713716D".lower()
ADDR_TETHER = "0xdac17f958d2ee523a2206206994597c13d831ec7".lower()
ADDR_USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48".lower()
ADDR_3CRV = "0x6c3f90f043a72fa612cbac8115ee7e52bde6e490".lower()
ADDR_WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2".lower()
ADDR_DAI = "0x6B175474E89094C44Da98b954EedeAC495271d0F".lower()


# Object for whitelisted silo token addresses 
ADDRS_SILO_TOKENS = Box(dict(
    # tokens 
    bean=ADDR_BEAN,
    bean_3crv=ADDR_BEAN_3CRV,
    ur_bean=ADDR_UR_BEAN, 
    ur_bean_3crv=ADDR_UR_BEAN_3CRV, 
    tether=ADDR_TETHER, 
    usdc=ADDR_USDC, 
    threecrv=ADDR_3CRV, 
    weth=ADDR_WETH, 
    dai=ADDR_DAI, 
))
# decimal numbers for silo tokens 
DECIMALS_SILO_TOKENS = Box(dict(
    bean=1e6, 
    bean_3crv=1e6, 
    ur_bean=1e6, 
    ur_bean_3crv=1e6, 
    tether=1e6, 
    usdc=1e6, 
    threecrv=1e18, 
    weth=1e18, 
    dai=1e18, 
))
# Object for all addresses 
ADDRS = Box(dict(
    # contracts 
    beanstalk=ADDR_BEANSTALK, 
    # tokens 
    **ADDRS_SILO_TOKENS,
))