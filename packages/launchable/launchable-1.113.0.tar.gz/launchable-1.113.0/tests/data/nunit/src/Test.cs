using System.Collections;
using NUnit.Framework;

namespace calc
{
    public class Tests1
    {
        [Test]
        public void Test1()
        {
            Assert.Pass();
        }

        [Test]
        public void Test2()
        {
            Assert.Fail("test 2 failed");
        }
    }

    public class Outer
    {
        public class Inner
        {
            [Test]
            public void Test3()
            {
                // this is how you access the inner class, but ...
                var x = new Outer.Inner();

                // you get the different type name
                Assert.That(typeof(Inner).Name, Is.EqualTo("Inner"));
                Assert.That(typeof(Inner).FullName, Is.EqualTo("calc.Outer+Inner"));
            }
        }
    }
}

namespace calc.sub
{
    public class Tests2
    {
        [Test]
        [Category("sub")]
        public void Foo() {}
    }
}


namespace ParameterizedTests
{
    [TestFixture]
    public class MyTests
    {
        [TestCaseSource(typeof(MyDataClass), nameof(MyDataClass.TestCases))]
        public int DivideTest(int n, int d)
        {
            return n / d;
        }
    }

    public class MyDataClass
    {
        public static IEnumerable TestCases
        {
            get
            {
                yield return new TestCaseData(12, 3).Returns(4);
                yield return new TestCaseData(12, 2).Returns(6);
                yield return new TestCaseData(12, 4).Returns(3);
            }
        }
    }
}
