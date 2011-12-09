# BK Precision 1696

This is a Python library for communicating with the [BK Precision 1696][psup]
power supply via its serial interface. You can control the supply's parameters
and take voltage/current readings.

For example:

    import psup
    with psup.Supply() as sup:
        sup.voltage(1.3)
        volts, amps = sup.reading()
        print '%f V, %f A' % (volts, amps)

For more details, see [my blog post][blog] about a setup using this library to
measure the dynamic power of a smartphone.

[psup]: http://www.bkprecision.com/products/model/1696/programmable-dc-power-supply-1-20vdc-0-999a.html
[blog]: http://www.cs.washington.edu/homes/asampson/blog/powermeasurement.html
